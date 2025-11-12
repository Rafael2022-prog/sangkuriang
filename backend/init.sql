-- SANGKURIANG Database Initialization Script

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_category ON projects(category);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);
CREATE INDEX IF NOT EXISTS idx_projects_deadline ON projects(deadline);
CREATE INDEX IF NOT EXISTS idx_funding_project_id ON funding(project_id);
CREATE INDEX IF NOT EXISTS idx_funding_user_id ON funding(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_requests_project_id ON audit_requests(project_id);
CREATE INDEX IF NOT EXISTS idx_audit_requests_status ON audit_requests(status);
CREATE INDEX IF NOT EXISTS idx_audit_results_request_id ON audit_results(request_id);

-- Create full-text search indexes
CREATE INDEX IF NOT EXISTS idx_projects_search ON projects USING gin(to_tsvector('english', title || ' ' || description));
CREATE INDEX IF NOT EXISTS idx_users_search ON users USING gin(to_tsvector('english', username || ' ' || email || ' ' || full_name));

-- Create function for updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_funding_updated_at BEFORE UPDATE ON funding
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_audit_requests_updated_at BEFORE UPDATE ON audit_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_audit_results_updated_at BEFORE UPDATE ON audit_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default admin user (password: admin123)
INSERT INTO users (id, username, email, full_name, hashed_password, role, is_active)
VALUES (
    uuid_generate_v4(),
    'admin',
    'admin@sangkuriang.local',
    'Administrator',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PJ/..G',
    'admin',
    true
) ON CONFLICT (email) DO NOTHING;

-- Insert sample categories
INSERT INTO project_categories (id, name, description, icon) VALUES
    (1, 'Cryptographic Algorithms', 'New encryption, hashing, or signature algorithms', '🔐'),
    (2, 'Blockchain Protocols', 'Distributed ledger and consensus mechanisms', '⛓️'),
    (3, 'Security Tools', 'Security analysis and penetration testing tools', '🛡️'),
    (4, 'Privacy Solutions', 'Privacy-preserving technologies and zero-knowledge proofs', '🔒'),
    (5, 'Quantum Cryptography', 'Post-quantum cryptographic algorithms', '⚛️'),
    (6, 'Authentication Systems', 'Multi-factor and biometric authentication', '🔑'),
    (7, 'Smart Contracts', 'Secure smart contract implementations', '📜'),
    (8, 'IoT Security', 'Internet of Things security solutions', '🌐')
ON CONFLICT DO NOTHING;

-- Insert sample tags
INSERT INTO project_tags (id, name, category) VALUES
    (1, 'encryption', 'cryptography'),
    (2, 'hashing', 'cryptography'),
    (3, 'signature', 'cryptography'),
    (4, 'blockchain', 'distributed'),
    (5, 'consensus', 'distributed'),
    (6, 'privacy', 'privacy'),
    (7, 'zero-knowledge', 'privacy'),
    (8, 'quantum', 'future'),
    (9, 'authentication', 'security'),
    (10, 'smart-contract', 'blockchain'),
    (11, 'iot', 'iot'),
    (12, 'malaysia', 'regional'),
    (13, 'indonesia', 'regional'),
    (14, 'asean', 'regional')
ON CONFLICT DO NOTHING;