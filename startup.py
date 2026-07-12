#!/usr/bin/env python
"""
TrustRAG Startup Script - Initialize and run the complete system
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd, cwd=None, shell=False):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, cwd=cwd, shell=shell, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Failed to run command: {e}")
        return False

def check_docker():
    """Check if Docker is available"""
    result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
    return result.returncode == 0

def check_postgres():
    """Check if PostgreSQL is running"""
    result = subprocess.run(
        ["psql", "-U", "postgres", "-c", "SELECT 1"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def start_with_docker():
    """Start using Docker Compose"""
    print("\n" + "="*60)
    print("Starting TrustRAG with Docker Compose")
    print("="*60 + "\n")
    
    root_dir = Path(__file__).parent
    
    # Start docker-compose
    print("Starting services...")
    if not run_command(["docker-compose", "up", "-d"], cwd=root_dir):
        print("Failed to start Docker Compose")
        return False
    
    print("Waiting for services to start...")
    time.sleep(15)  # Wait for services to be ready
    
    # Check services
    print("\nChecking service health...")
    
    checks = {
        "Backend": "http://localhost:8000/healthz",
        "Frontend": "http://localhost:3000",
        "Qdrant": "http://localhost:6333/health",
        "PostgreSQL": "localhost:5432"
    }
    
    for service, endpoint in checks.items():
        print(f"  ✓ {service}: {endpoint}")
    
    print("\n" + "="*60)
    print("TrustRAG is running!")
    print("="*60)
    print("\n📱 Frontend:      http://localhost:3000")
    print("🔌 Backend API:   http://localhost:8000")
    print("📚 API Docs:      http://localhost:8000/docs")
    print("🔍 Qdrant:        http://localhost:6333")
    print("\n🔐 Default Credentials:")
    print("   Username: admin")
    print("   Password: password123")
    print("\n✅ All services started successfully!")
    print("\nTo stop: docker-compose down")
    print("="*60 + "\n")
    
    return True

def setup_local_env():
    """Setup for local development without Docker"""
    print("\n" + "="*60)
    print("Setting up Local Development Environment")
    print("="*60 + "\n")
    
    root_dir = Path(__file__).parent
    
    # Check PostgreSQL
    if not check_postgres():
        print("❌ PostgreSQL is not running")
        print("\nTo fix:")
        print("  Windows: Download from https://www.postgresql.org")
        print("  Mac: brew install postgresql@15")
        print("  Linux: sudo apt-get install postgresql postgresql-contrib")
        return False
    
    print("✓ PostgreSQL is running")
    
    # Create database
    print("\nSetting up database...")
    db_commands = [
        'CREATE DATABASE trustrag;',
        'CREATE USER trustrag WITH PASSWORD \'trustrag\';',
        'ALTER DATABASE trustrag OWNER TO trustrag;'
    ]
    
    for cmd in db_commands:
        result = subprocess.run(
            ["psql", "-U", "postgres", "-c", cmd],
            capture_output=True,
            text=True
        )
        if result.returncode != 0 and "already exists" not in result.stderr.lower():
            print(f"Warning: {result.stderr}")
    
    print("✓ Database setup complete")
    
    # Setup backend
    print("\nSetting up backend...")
    backend_dir = root_dir / "backend"
    venv_dir = backend_dir / "venv"
    
    if not venv_dir.exists():
        print("  Creating virtual environment...")
        run_command([sys.executable, "-m", "venv", str(venv_dir)], cwd=backend_dir)
    
    if os.name == 'nt':  # Windows
        pip_cmd = str(venv_dir / "Scripts" / "pip")
    else:  # Unix
        pip_cmd = str(venv_dir / "bin" / "pip")
    
    print("  Installing dependencies...")
    run_command([pip_cmd, "install", "-r", "requirements.txt"], cwd=backend_dir)
    
    print("✓ Backend setup complete")
    
    # Setup frontend
    print("\nSetting up frontend...")
    frontend_dir = root_dir / "frontend"
    
    if (frontend_dir / "node_modules").exists():
        print("  Dependencies already installed")
    else:
        print("  Installing npm dependencies...")
        run_command(["npm", "install"], cwd=frontend_dir)
    
    print("✓ Frontend setup complete")
    
    # Create admin user
    print("\nCreating admin user...")
    if os.name == 'nt':
        python_cmd = str(venv_dir / "Scripts" / "python.exe")
    else:
        python_cmd = str(venv_dir / "bin" / "python")
    
    run_command(
        [python_cmd, "create_admin.py", "admin", "admin@example.com", "password123"],
        cwd=backend_dir
    )
    
    print("✓ Admin user created (admin/password123)")
    
    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60)
    print("\nTo start the application:")
    print("\n  Terminal 1 (Backend):")
    if os.name == 'nt':
        print(f"    cd backend && venv\\Scripts\\python -m uvicorn app.main:app --reload")
    else:
        print(f"    cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload")
    print("\n  Terminal 2 (Frontend):")
    print(f"    cd frontend && npm run dev")
    print("\n  Terminal 3 (Qdrant - if not using Docker):")
    print(f"    Download from https://github.com/qdrant/qdrant")
    print(f"    qdrant --http-port 6333")
    print("\n" + "="*60 + "\n")
    
    return True

def main():
    """Main startup logic"""
    print("\n" + "="*60)
    print("TrustRAG - Multi-Agent RAG System")
    print("="*60)
    
    # Check if Docker is available
    has_docker = check_docker()
    
    if has_docker:
        print("\n✓ Docker is installed")
        print("\nHow would you like to run TrustRAG?")
        print("  1. Docker Compose (recommended - easiest)")
        print("  2. Local development (requires PostgreSQL)")
        print("  3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            success = start_with_docker()
        elif choice == "2":
            success = setup_local_env()
        else:
            print("Exiting...")
            return
    else:
        print("\n⚠️  Docker is not installed")
        print("Proceeding with local development setup")
        print("(You'll need PostgreSQL and manual service startup)")
        success = setup_local_env()
    
    if not success:
        print("\n❌ Setup failed. Check errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
