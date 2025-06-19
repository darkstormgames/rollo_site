"""Example script to demonstrate JWT authentication endpoints."""

import asyncio
import requests
import json
from typing import Dict, Any


class AuthAPIDemo:
    """Demo class for testing authentication endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
    
    def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user."""
        data = {
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": password
        }
        
        response = requests.post(f"{self.base_url}/api/auth/register", json=data)
        if response.status_code == 200:
            result = response.json()
            self.access_token = result["tokens"]["access_token"]
            self.refresh_token = result["tokens"]["refresh_token"]
            print(f"✅ User '{username}' registered successfully")
            return result
        else:
            print(f"❌ Registration failed: {response.json()}")
            return response.json()
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """Login user."""
        data = {
            "username": username,
            "password": password
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=data)
        if response.status_code == 200:
            result = response.json()
            self.access_token = result["tokens"]["access_token"]
            self.refresh_token = result["tokens"]["refresh_token"]
            print(f"✅ User '{username}' logged in successfully")
            return result
        else:
            print(f"❌ Login failed: {response.json()}")
            return response.json()
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get current user profile."""
        if not self.access_token:
            print("❌ No access token available")
            return {}
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Got user profile: {result['username']}")
            return result
        else:
            print(f"❌ Failed to get profile: {response.json()}")
            return response.json()
    
    def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh access token."""
        if not self.refresh_token:
            print("❌ No refresh token available")
            return {}
        
        data = {"refresh_token": self.refresh_token}
        response = requests.post(f"{self.base_url}/api/auth/refresh", json=data)
        
        if response.status_code == 200:
            result = response.json()
            self.access_token = result["access_token"]
            print("✅ Access token refreshed successfully")
            return result
        else:
            print(f"❌ Token refresh failed: {response.json()}")
            return response.json()
    
    def logout_user(self) -> Dict[str, Any]:
        """Logout user."""
        if not self.access_token or not self.refresh_token:
            print("❌ No tokens available")
            return {}
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        data = {"refresh_token": self.refresh_token}
        response = requests.post(f"{self.base_url}/api/auth/logout", json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            self.access_token = None
            self.refresh_token = None
            print("✅ Logged out successfully")
            return result
        else:
            print(f"❌ Logout failed: {response.json()}")
            return response.json()
    
    def test_protected_endpoint_without_auth(self):
        """Test accessing protected endpoint without authentication."""
        response = requests.get(f"{self.base_url}/api/auth/me")
        print(f"🔒 Accessing /me without auth: {response.status_code} - {response.json().get('detail', 'No detail')}")
    
    def request_password_reset(self, email: str) -> Dict[str, Any]:
        """Request password reset."""
        data = {"email": email}
        response = requests.post(f"{self.base_url}/api/auth/forgot-password", json=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Password reset requested for {email}")
            return result
        else:
            print(f"❌ Password reset request failed: {response.json()}")
            return response.json()


def demo_flow():
    """Demonstrate the authentication flow."""
    print("🚀 JWT Authentication Demo")
    print("=" * 50)
    
    demo = AuthAPIDemo()
    
    # Test 1: Try to access protected endpoint without auth
    print("\n1. Testing protected endpoint without authentication:")
    demo.test_protected_endpoint_without_auth()
    
    # Test 2: Register a new user
    print("\n2. Registering a new user:")
    demo.register_user("demouser", "demo@example.com", "DemoPass123!")
    
    # Test 3: Get user profile
    print("\n3. Getting user profile:")
    demo.get_current_user()
    
    # Test 4: Refresh token
    print("\n4. Refreshing access token:")
    demo.refresh_access_token()
    
    # Test 5: Get profile with new token
    print("\n5. Getting profile with refreshed token:")
    demo.get_current_user()
    
    # Test 6: Request password reset
    print("\n6. Requesting password reset:")
    demo.request_password_reset("demo@example.com")
    
    # Test 7: Logout
    print("\n7. Logging out:")
    demo.logout_user()
    
    # Test 8: Try to access protected endpoint after logout
    print("\n8. Testing protected endpoint after logout:")
    demo.test_protected_endpoint_without_auth()
    
    # Test 9: Login again
    print("\n9. Logging in again:")
    demo.login_user("demouser", "DemoPass123!")
    
    print("\n✅ Demo completed successfully!")
    print("\nAPI Endpoints implemented:")
    print("- POST /api/auth/register - User registration")
    print("- POST /api/auth/login - User login")
    print("- POST /api/auth/logout - User logout")
    print("- POST /api/auth/refresh - Refresh access token")
    print("- POST /api/auth/forgot-password - Request password reset")
    print("- POST /api/auth/reset-password - Reset password with token")
    print("- GET /api/auth/me - Get current user profile")


if __name__ == "__main__":
    print("To run this demo:")
    print("1. Start the FastAPI server: uvicorn app:app --reload")
    print("2. Run this script: python demo_auth.py")
    print("3. Ensure the database is set up with proper tables")
    
    # Uncomment the line below to run the demo
    # demo_flow()