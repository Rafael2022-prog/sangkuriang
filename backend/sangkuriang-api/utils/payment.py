import asyncio
import aiohttp
import json
import hmac
import hashlib
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import os

class PaymentGateway:
    """Base class for payment gateways."""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
    
    async def create_payment(self, amount: float, payment_method: str, **kwargs) -> Dict[str, Any]:
        """Create a payment."""
        raise NotImplementedError
    
    async def check_payment_status(self, payment_id: str) -> str:
        """Check payment status."""
        raise NotImplementedError
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """Cancel a payment."""
        raise NotImplementedError
    
    async def process_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment callback."""
        raise NotImplementedError

class MidtransGateway(PaymentGateway):
    """Midtrans payment gateway integration."""
    
    def __init__(self, config: Dict[str, str]):
        super().__init__(config)
        self.server_key = config.get("server_key", "")
        self.client_key = config.get("client_key", "")
        self.environment = config.get("environment", "sandbox")
        self.base_url = "https://api.midtrans.com" if self.environment == "production" else "https://api.sandbox.midtrans.com"
    
    def generate_signature(self, order_id: str, status_code: str, gross_amount: str) -> str:
        """Generate Midtrans signature."""
        string_to_hash = f"{order_id}{status_code}{gross_amount}{self.server_key}"
        return hashlib.sha512(string_to_hash.encode()).hexdigest()
    
    async def create_payment(self, amount: float, payment_method: str, **kwargs) -> Dict[str, Any]:
        """Create payment with Midtrans."""
        
        order_id = kwargs.get("order_id", str(uuid.uuid4()))
        customer_details = kwargs.get("customer_details", {})
        
        payload = {
            "transaction_details": {
                "order_id": order_id,
                "gross_amount": int(amount)  # Midtrans requires integer
            },
            "customer_details": {
                "first_name": customer_details.get("first_name", "User"),
                "last_name": customer_details.get("last_name", ""),
                "email": customer_details.get("email", ""),
                "phone": customer_details.get("phone", "")
            }
        }
        
        # Add payment method specific details
        if payment_method == "bank_transfer":
            payload["payment_type"] = "bank_transfer"
            payload["bank_transfer"] = {
                "bank": kwargs.get("bank", "bca")  # Default to BCA
            }
        elif payment_method == "gopay":
            payload["payment_type"] = "gopay"
        elif payment_method == "shopeepay":
            payload["payment_type"] = "shopeepay"
        elif payment_method == "qris":
            payload["payment_type"] = "qris"
        else:
            payload["payment_type"] = payment_method
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {base64.b64encode(self.server_key.encode()).decode()}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v2/charge",
                json=payload,
                headers=headers
            ) as response:
                result = await response.json()
                
                if response.status == 200 or response.status == 201:
                    return {
                        "success": True,
                        "gateway_payment_id": result.get("transaction_id"),
                        "payment_url": result.get("redirect_url"),
                        "va_number": result.get("va_numbers", [{}])[0].get("va_number") if result.get("va_numbers") else None,
                        "qr_code": result.get("qr_string") if payment_method == "qris" else None,
                        "status": result.get("transaction_status", "pending"),
                        "raw_response": result
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("status_message", "Unknown error"),
                        "raw_response": result
                    }
    
    async def check_payment_status(self, payment_id: str) -> str:
        """Check Midtrans payment status."""
        headers = {
            "Accept": "application/json",
            "Authorization": f"Basic {base64.b64encode(self.server_key.encode()).decode()}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/v2/{payment_id}/status",
                headers=headers
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    return result.get("transaction_status", "unknown")
                return "unknown"
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """Cancel Midtrans payment."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {base64.b64encode(self.server_key.encode()).decode()}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v2/{payment_id}/cancel",
                headers=headers
            ) as response:
                return response.status == 200
    
    async def process_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Midtrans callback."""
        # Verify signature
        order_id = callback_data.get("order_id", "")
        status_code = callback_data.get("status_code", "")
        gross_amount = callback_data.get("gross_amount", "")
        signature_key = callback_data.get("signature_key", "")
        
        expected_signature = hashlib.sha512(
            f"{order_id}{status_code}{gross_amount}{self.server_key}".encode()
        ).hexdigest()
        
        if signature_key != expected_signature:
            return {
                "success": False,
                "error": "Invalid signature"
            }
        
        return {
            "success": True,
            "gateway_payment_id": callback_data.get("transaction_id"),
            "status": callback_data.get("transaction_status"),
            "raw_data": callback_data
        }

class XenditGateway(PaymentGateway):
    """Xendit payment gateway integration."""
    
    def __init__(self, config: Dict[str, str]):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.environment = config.get("environment", "sandbox")
        self.base_url = "https://api.xendit.co" if self.environment == "production" else "https://api.xendit.co"
    
    async def create_payment(self, amount: float, payment_method: str, **kwargs) -> Dict[str, Any]:
        """Create payment with Xendit."""
        
        external_id = kwargs.get("external_id", str(uuid.uuid4()))
        customer_details = kwargs.get("customer_details", {})
        
        payload = {
            "external_id": external_id,
            "amount": amount,
            "description": kwargs.get("description", "Sangkuriang Payment"),
            "invoice_duration": 86400,  # 24 hours
            "customer": {
                "given_names": customer_details.get("first_name", "User"),
                "surname": customer_details.get("last_name", ""),
                "email": customer_details.get("email", ""),
                "mobile_number": customer_details.get("phone", "")
            }
        }
        
        headers = {
            "Authorization": f"Basic {base64.b64encode(self.api_key.encode()).decode()}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            if payment_method == "virtual_account":
                # Create fixed virtual account
                va_payload = {
                    "external_id": external_id,
                    "bank_code": kwargs.get("bank", "BNI"),
                    "name": f"{customer_details.get('first_name', 'User')} {customer_details.get('last_name', '')}".strip()
                }
                
                async with session.post(
                    f"{self.base_url}/callback_virtual_accounts",
                    json=va_payload,
                    headers=headers
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        return {
                            "success": True,
                            "gateway_payment_id": result.get("id"),
                            "va_number": result.get("account_number"),
                            "status": "pending",
                            "raw_response": result
                        }
            
            else:
                # Create invoice
                async with session.post(
                    f"{self.base_url}/v2/invoices",
                    json=payload,
                    headers=headers
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200 or response.status == 201:
                        return {
                            "success": True,
                            "gateway_payment_id": result.get("id"),
                            "payment_url": result.get("invoice_url"),
                            "status": result.get("status", "pending"),
                            "raw_response": result
                        }
                    else:
                        return {
                            "success": False,
                            "error": result.get("message", "Unknown error"),
                            "raw_response": result
                        }
    
    async def check_payment_status(self, payment_id: str) -> str:
        """Check Xendit payment status."""
        headers = {
            "Authorization": f"Basic {base64.b64encode(self.api_key.encode()).decode()}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/v2/invoices/{payment_id}",
                headers=headers
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    return result.get("status", "unknown")
                return "unknown"
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """Cancel Xendit payment."""
        headers = {
            "Authorization": f"Basic {base64.b64encode(self.api_key.encode()).decode()}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v2/invoices/{payment_id}/expire!",
                headers=headers
            ) as response:
                return response.status == 200
    
    async def process_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Xendit callback."""
        # Xendit uses webhook signature verification
        # This is a simplified version - in production, implement proper signature verification
        
        return {
            "success": True,
            "gateway_payment_id": callback_data.get("id"),
            "status": callback_data.get("status"),
            "raw_data": callback_data
        }

class PaymentProcessor:
    """Payment processor that handles multiple gateways."""
    
    def __init__(self):
        self.gateways = {}
        self.load_gateways()
    
    def load_gateways(self):
        """Load payment gateway configurations."""
        # Midtrans configuration
        midtrans_config = {
            "server_key": os.getenv("MIDTRANS_SERVER_KEY", "SB-Mid-server-xxxxxxxx"),
            "client_key": os.getenv("MIDTRANS_CLIENT_KEY", "SB-Mid-client-xxxxxxxx"),
            "environment": os.getenv("MIDTRANS_ENVIRONMENT", "sandbox")
        }
        self.gateways["midtrans"] = MidtransGateway(midtrans_config)
        
        # Xendit configuration
        xendit_config = {
            "api_key": os.getenv("XENDIT_API_KEY", "xnd_development_xxxxxxxx"),
            "environment": os.getenv("XENDIT_ENVIRONMENT", "sandbox")
        }
        self.gateways["xendit"] = XenditGateway(xendit_config)
    
    async def get_available_methods(self, country: str = "ID") -> List[Dict[str, Any]]:
        """Get available payment methods."""
        methods = [
            {
                "id": "gopay",
                "name": "GoPay",
                "type": "e_wallet",
                "gateway": "midtrans",
                "icon": "gopay.png",
                "description": "Pay with GoPay e-wallet",
                "supported_countries": ["ID"]
            },
            {
                "id": "shopeepay",
                "name": "ShopeePay",
                "type": "e_wallet",
                "gateway": "midtrans",
                "icon": "shopeepay.png",
                "description": "Pay with ShopeePay e-wallet",
                "supported_countries": ["ID"]
            },
            {
                "id": "bank_transfer_bca",
                "name": "Bank Transfer BCA",
                "type": "bank_transfer",
                "gateway": "midtrans",
                "icon": "bca.png",
                "description": "Transfer to BCA Virtual Account",
                "supported_countries": ["ID"]
            },
            {
                "id": "bank_transfer_bni",
                "name": "Bank Transfer BNI",
                "type": "bank_transfer",
                "gateway": "xendit",
                "icon": "bni.png",
                "description": "Transfer to BNI Virtual Account",
                "supported_countries": ["ID"]
            },
            {
                "id": "bank_transfer_mandiri",
                "name": "Bank Transfer Mandiri",
                "type": "bank_transfer",
                "gateway": "midtrans",
                "icon": "mandiri.png",
                "description": "Transfer to Mandiri Virtual Account",
                "supported_countries": ["ID"]
            },
            {
                "id": "qris",
                "name": "QRIS",
                "type": "qr_code",
                "gateway": "midtrans",
                "icon": "qris.png",
                "description": "Pay with QRIS code",
                "supported_countries": ["ID"]
            }
        ]
        
        # Filter by country
        if country:
            methods = [m for m in methods if country in m.get("supported_countries", [])]
        
        return methods
    
    async def create_payment(
        self, 
        payment_id: str,
        amount: float, 
        payment_method: str, 
        payment_gateway: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create payment with specified gateway."""
        
        gateway = self.gateways.get(payment_gateway.lower())
        if not gateway:
            return {
                "success": False,
                "error": f"Payment gateway '{payment_gateway}' not supported"
            }
        
        try:
            # Extract bank code if present
            bank_code = None
            if "bank_transfer" in payment_method:
                bank_code = payment_method.replace("bank_transfer_", "")
                payment_method = "bank_transfer" if payment_gateway == "midtrans" else "virtual_account"
            
            # Add order ID and other required fields
            kwargs["order_id"] = payment_id
            kwargs["external_id"] = payment_id
            kwargs["bank"] = bank_code
            
            result = await gateway.create_payment(amount, payment_method, **kwargs)
            
            # Add payment ID to result
            result["payment_id"] = payment_id
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Payment creation failed: {str(e)}"
            }
    
    async def check_payment_status(self, gateway_payment_id: str, payment_gateway: str) -> str:
        """Check payment status with specified gateway."""
        
        gateway = self.gateways.get(payment_gateway.lower())
        if not gateway:
            return "unknown"
        
        try:
            return await gateway.check_payment_status(gateway_payment_id)
        except Exception:
            return "unknown"
    
    async def cancel_payment(self, gateway_payment_id: str, payment_gateway: str) -> bool:
        """Cancel payment with specified gateway."""
        
        gateway = self.gateways.get(payment_gateway.lower())
        if not gateway:
            return False
        
        try:
            return await gateway.cancel_payment(gateway_payment_id)
        except Exception:
            return False
    
    async def process_callback(self, gateway: str, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment callback from gateway."""
        
        gateway_instance = self.gateways.get(gateway.lower())
        if not gateway_instance:
            return {
                "success": False,
                "error": f"Payment gateway '{gateway}' not supported"
            }
        
        try:
            return await gateway_instance.process_callback(callback_data)
        except Exception as e:
            return {
                "success": False,
                "error": f"Callback processing failed: {str(e)}"
            }