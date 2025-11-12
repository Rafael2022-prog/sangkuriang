from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from database import get_db
from models.project import Project, ProjectFunding
from models.payment import Payment, PaymentMethod
from models.user import User
from schemas.payment import (
    PaymentMethodResponse, PaymentRequest, PaymentResponse,
    PaymentStatusResponse, PaymentCallbackData
)
from utils.security import get_current_user
from utils.payment import PaymentProcessor, PaymentGateway
import uuid
from datetime import datetime, timedelta
import json

router = APIRouter(prefix="/payments", tags=["payments"])

@router.get("/methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(
    country: Optional[str] = "ID",
    db: Session = Depends(get_db)
):
    """Get available payment methods."""
    payment_processor = PaymentProcessor()
    methods = await payment_processor.get_available_methods(country=country)
    
    return methods

@router.post("/create", response_model=PaymentResponse)
async def create_payment(
    payment_data: PaymentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new payment."""
    # Verify project exists
    project = db.query(Project).filter(Project.id == payment_data.project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify funding record exists
    funding = db.query(ProjectFunding).filter(
        ProjectFunding.id == payment_data.funding_id,
        ProjectFunding.user_id == current_user.id
    ).first()
    
    if not funding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Funding record not found"
        )
    
    if funding.payment_status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already processed for this funding"
        )
    
    # Create payment record
    payment = Payment(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        project_id=payment_data.project_id,
        funding_id=payment_data.funding_id,
        amount=funding.amount,
        payment_method=payment_data.payment_method,
        payment_gateway=payment_data.payment_gateway,
        status="pending",
        currency="IDR",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
    )
    
    db.add(payment)
    
    # Initialize payment processor
    payment_processor = PaymentProcessor()
    
    try:
        # Create payment with gateway
        gateway_response = await payment_processor.create_payment(
            payment_id=payment.id,
            amount=funding.amount,
            payment_method=payment_data.payment_method,
            payment_gateway=payment_data.payment_gateway,
            user_email=current_user.email,
            user_phone=current_user.phone,
            project_name=project.title
        )
        
        # Update payment with gateway response
        payment.gateway_payment_id = gateway_response.get("gateway_payment_id")
        payment.gateway_response = gateway_response
        payment.payment_url = gateway_response.get("payment_url")
        payment.qr_code = gateway_response.get("qr_code")
        payment.va_number = gateway_response.get("va_number")
        payment.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(payment)
        
        # Schedule payment expiry check
        background_tasks.add_task(check_payment_expiry, payment.id)
        
        return payment
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment: {str(e)}"
        )

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get payment details."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Check authorization
    if payment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this payment"
        )
    
    return payment

@router.get("/{payment_id}/status", response_model=PaymentStatusResponse)
async def get_payment_status(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get payment status."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Check authorization
    if payment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this payment"
        )
    
    # Check with payment gateway for latest status
    if payment.status in ["pending", "processing"]:
        payment_processor = PaymentProcessor()
        try:
            gateway_status = await payment_processor.check_payment_status(
                payment.gateway_payment_id,
                payment.payment_gateway
            )
            
            if gateway_status != payment.status:
                await update_payment_status(payment.id, gateway_status, db)
                payment.status = gateway_status
                payment.updated_at = datetime.utcnow()
                db.commit()
                
        except Exception as e:
            # Log error but don't fail the request
            print(f"Error checking payment status: {e}")
    
    return {
        "payment_id": payment_id,
        "status": payment.status,
        "gateway_status": payment.gateway_response.get("status") if payment.gateway_response else None,
        "paid_at": payment.paid_at,
        "expires_at": payment.expires_at
    }

@router.post("/{payment_id}/cancel")
async def cancel_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a pending payment."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Check authorization
    if payment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this payment"
        )
    
    if payment.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel payment in current status"
        )
    
    # Cancel with payment gateway
    payment_processor = PaymentProcessor()
    try:
        await payment_processor.cancel_payment(
            payment.gateway_payment_id,
            payment.payment_gateway
        )
        
        payment.status = "cancelled"
        payment.updated_at = datetime.utcnow()
        
        # Update funding status
        funding = db.query(ProjectFunding).filter(
            ProjectFunding.id == payment.funding_id
        ).first()
        
        if funding:
            funding.payment_status = "cancelled"
            
            # Update project funding
            project = db.query(Project).filter(
                Project.id == payment.project_id
            ).first()
            
            if project:
                project.current_funding -= funding.amount
                project.backer_count = max(0, project.backer_count - 1)
                project.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Payment cancelled successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel payment: {str(e)}"
        )

@router.post("/callback/{gateway}")
async def payment_callback(
    gateway: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle payment gateway callbacks."""
    try:
        # Get callback data
        callback_data = await request.json()
        
        # Process callback based on gateway
        payment_processor = PaymentProcessor()
        processed_data = await payment_processor.process_callback(gateway, callback_data)
        
        # Find payment by gateway ID
        payment = db.query(Payment).filter(
            Payment.gateway_payment_id == processed_data["gateway_payment_id"],
            Payment.payment_gateway == gateway
        ).first()
        
        if not payment:
            return {"status": "error", "message": "Payment not found"}
        
        # Update payment status
        if processed_data["status"] != payment.status:
            await update_payment_status(payment.id, processed_data["status"], db)
            
            # Store callback data
            payment.callback_data = processed_data["raw_data"]
            payment.updated_at = datetime.utcnow()
            db.commit()
        
        return {"status": "success"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/user/{user_id}/history")
async def get_user_payment_history(
    user_id: str,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user payment history."""
    # Check authorization
    if user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's payment history"
        )
    
    # Get payments
    query = db.query(Payment).filter(Payment.user_id == user_id)
    
    total = query.count()
    payments = query.order_by(Payment.created_at.desc()).offset(
        (page - 1) * limit
    ).limit(limit).all()
    
    return {
        "items": payments,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }

@router.get("/stats/summary")
async def get_payment_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get payment statistics."""
    # Check if admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view payment statistics"
        )
    
    from datetime import datetime, timedelta
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get statistics
    total_payments = db.query(Payment).filter(Payment.created_at >= start_date).count()
    
    successful_payments = db.query(Payment).filter(
        Payment.created_at >= start_date,
        Payment.status == "completed"
    ).count()
    
    total_amount = db.query(func.sum(Payment.amount)).filter(
        Payment.created_at >= start_date,
        Payment.status == "completed"
    ).scalar() or 0
    
    # Get daily stats
    daily_stats = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        next_date = date + timedelta(days=1)
        
        day_payments = db.query(Payment).filter(
            Payment.created_at >= date,
            Payment.created_at < next_date
        ).count()
        
        day_amount = db.query(func.sum(Payment.amount)).filter(
            Payment.created_at >= date,
            Payment.created_at < next_date,
            Payment.status == "completed"
        ).scalar() or 0
        
        daily_stats.append({
            "date": date.strftime("%Y-%m-%d"),
            "payments": day_payments,
            "amount": float(day_amount)
        })
    
    return {
        "total_payments": total_payments,
        "successful_payments": successful_payments,
        "success_rate": round((successful_payments / total_payments * 100) if total_payments > 0 else 0, 2),
        "total_amount": float(total_amount),
        "daily_stats": daily_stats
    }

async def update_payment_status(payment_id: str, new_status: str, db: Session):
    """Update payment status and related records."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        return
    
    old_status = payment.status
    payment.status = new_status
    
    if new_status == "completed":
        payment.paid_at = datetime.utcnow()
        
        # Update funding status
        funding = db.query(ProjectFunding).filter(
            ProjectFunding.id == payment.funding_id
        ).first()
        
        if funding:
            funding.payment_status = "completed"
            
            # Update project statistics
            project = db.query(Project).filter(
                Project.id == payment.project_id
            ).first()
            
            if project:
                project.current_funding += funding.amount
                project.backer_count += 1
                
                # Check if project is fully funded
                if project.current_funding >= project.funding_goal:
                    project.status = "funded"
                
                project.updated_at = datetime.utcnow()
    
    elif new_status in ["failed", "cancelled", "expired"]:
        # Update funding status
        funding = db.query(ProjectFunding).filter(
            ProjectFunding.id == payment.funding_id
        ).first()
        
        if funding:
            funding.payment_status = new_status
            
            # Revert project funding if it was previously completed
            if old_status == "completed":
                project = db.query(Project).filter(
                    Project.id == payment.project_id
                ).first()
                
                if project:
                    project.current_funding = max(0, project.current_funding - funding.amount)
                    project.backer_count = max(0, project.backer_count - 1)
                    project.updated_at = datetime.utcnow()
    
    payment.updated_at = datetime.utcnow()
    db.commit()

async def check_payment_expiry(payment_id: str):
    """Check and handle payment expiry."""
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        
        if payment and payment.status == "pending" and payment.expires_at < datetime.utcnow():
            await update_payment_status(payment_id, "expired", db)
            
    finally:
        db.close()