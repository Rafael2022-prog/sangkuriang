#!/usr/bin/env python3
"""Debug script untuk melihat struktur proposal_dict"""

import sys
sys.path.insert(0, '.')
from dao.governance import Proposal, ProposalStatus
from datetime import datetime, timedelta
from decimal import Decimal

# Buat proposal seperti di fixture
proposal = Proposal(
    proposal_id='prop_123456789',
    title='Proposal Pengembangan Sistem Kriptografi Baru',
    description='Mengusulkan pengembangan sistem kriptografi berbasis matematika Nusantara untuk meningkatkan keamanan data komunitas SANGKURIANG.',
    proposer='0x1111111111111111111111111111111111111111',
    category='technical',
    status=ProposalStatus.ACTIVE,
    created_at=datetime.now(),
    voting_start_time=datetime.now(),
    voting_end_time=datetime.now() + timedelta(days=7),
    execution_time=None,
    votes_for=Decimal('0.0'),
    votes_against=Decimal('0.0'),
    votes_abstain=Decimal('0.0'),
    total_votes=Decimal('0.0'),
    quorum_required=Decimal('1000.0')
)

# Test to_dict
proposal_dict = proposal.to_dict()
print('Proposal dict keys:', list(proposal_dict.keys()))
print('Required fields check:')
required_fields = ['proposal_id', 'title', 'description', 'proposer', 'category', 'status', 'created_at', 'voting_start_time', 'voting_end_time']
for field in required_fields:
    print(f'  {field}: {"✓" if field in proposal_dict else "✗"}')
    if field in proposal_dict:
        print(f'    type: {type(proposal_dict[field])}')
        if isinstance(proposal_dict[field], str):
            print(f'    value: {proposal_dict[field][:50]}')
        else:
            print(f'    value: {proposal_dict[field]}')

# Test from_dict
print('\nTesting from_dict...')
try:
    reconstructed = Proposal.from_dict(proposal_dict)
    print('✓ from_dict berhasil')
except Exception as e:
    print(f'✗ from_dict gagal: {e}')