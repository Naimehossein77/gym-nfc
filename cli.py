#!/usr/bin/env python3
"""
Gym NFC Management System - Command Line Interface

This script provides a command-line interface for testing and managing
the NFC card assignment system without needing to use the REST API directly.
"""

import asyncio
import requests
import json
import getpass
import sys
from typing import Optional
import argparse


class GymNFCClient:
    """Command-line client for the Gym NFC Management System"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.token: Optional[str] = None
        self.session = requests.Session()
    
    def login(self, username: str, password: str) -> bool:
        """Login and get JWT token"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                data={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                print(f"✅ Successfully logged in as {username}")
                return True
            else:
                print(f"❌ Login failed: {response.json().get('detail', 'Unknown error')}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def search_members(self, query: str, limit: int = 10) -> None:
        """Search for members"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/members/search",
                json={"query": query, "limit": limit}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n🔍 Found {data['total']} members matching '{query}':")
                print("-" * 80)
                
                for member in data['members']:
                    print(f"ID: {member['id']:4} | Name: {member['name']:20} | "
                          f"Email: {member['email']:25} | Status: {member['status']}")
                
                if data['total'] > limit:
                    print(f"\n... and {data['total'] - limit} more results")
                    
            else:
                print(f"❌ Search failed: {response.json().get('detail', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
    
    def generate_token(self, member_id: int, expires_in_days: Optional[int] = None) -> Optional[str]:
        """Generate a token for a member"""
        try:
            payload = {"member_id": member_id}
            if expires_in_days:
                payload["expires_in_days"] = expires_in_days
            
            response = self.session.post(
                f"{self.base_url}/api/tokens/generate",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data["token"]
                print(f"✅ Generated token for member {member_id}: {token}")
                
                if data.get("expires_at"):
                    print(f"   Expires: {data['expires_at']}")
                else:
                    print("   No expiration")
                    
                return token
            else:
                print(f"❌ Token generation failed: {response.json().get('detail', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return None
    
    def write_token_to_card(self, token: str, member_id: int) -> bool:
        """Write token to NFC card"""
        try:
            print(f"📡 Starting NFC write operation...")
            print(f"   Token: {token}")
            print(f"   Member ID: {member_id}")
            print(f"   📋 Please place an NFC card on the reader now...")
            
            response = self.session.post(
                f"{self.base_url}/api/nfc/write",
                json={"token": token, "member_id": member_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {data['message']}")
                if data.get('card_id'):
                    print(f"   Card ID: {data['card_id']}")
                return True
            else:
                print(f"❌ NFC write failed: {response.json().get('detail', 'Unknown error')}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def check_nfc_status(self) -> None:
        """Check NFC reader status"""
        try:
            response = self.session.get(f"{self.base_url}/api/nfc/status")
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    print(f"✅ {data['message']}")
                    if data.get('data'):
                        reader_data = data['data']
                        print(f"   Status: {reader_data.get('status', 'unknown')}")
                        print(f"   Reader: {reader_data.get('reader_type', 'unknown')}")
                        print(f"   Timeout: {reader_data.get('timeout', 'unknown')}s")
                else:
                    print(f"❌ {data['message']}")
            else:
                print(f"❌ Status check failed: {response.json().get('detail', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
    
    def read_card(self) -> None:
        """Read data from NFC card"""
        try:
            print(f"📡 Starting NFC read operation...")
            print(f"   📋 Please place an NFC card on the reader now...")
            
            response = self.session.get(f"{self.base_url}/api/nfc/read")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {data['message']}")
                
                if data.get('data') and data['data'].get('content'):
                    card_data = data['data']
                    print(f"   Card ID: {card_data['card_id']}")
                    print(f"   Content: {card_data['content']}")
                    print(f"   Records: {card_data['records_count']}")
                elif data.get('data'):
                    print(f"   Card ID: {data['data']['card_id']}")
                    print(f"   No data found on card")
            else:
                print(f"❌ NFC read failed: {response.json().get('detail', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")


def interactive_mode(client: GymNFCClient) -> None:
    """Interactive command-line mode"""
    
    print("\n🏋️ Gym NFC Management System - Interactive Mode")
    print("=" * 60)
    
    # Login
    while not client.token:
        print("\nPlease login:")
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        
        if not client.login(username, password):
            choice = input("\nTry again? (y/n): ").strip().lower()
            if choice != 'y':
                return
    
    # Main menu loop
    while True:
        print("\n" + "=" * 60)
        print("Main Menu:")
        print("1. Search members")
        print("2. Generate token for member")
        print("3. Write token to NFC card")
        print("4. Read NFC card")
        print("5. Check NFC reader status")
        print("6. Complete workflow (search → generate → write)")
        print("7. Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == '1':
            query = input("Enter search query (name, email, phone, or ID): ").strip()
            if query:
                client.search_members(query)
        
        elif choice == '2':
            try:
                member_id = int(input("Enter member ID: ").strip())
                expires = input("Expires in days (press Enter for no expiration): ").strip()
                expires_days = int(expires) if expires else None
                client.generate_token(member_id, expires_days)
            except ValueError:
                print("❌ Invalid member ID or expiration days")
        
        elif choice == '3':
            token = input("Enter token: ").strip()
            try:
                member_id = int(input("Enter member ID: ").strip())
                client.write_token_to_card(token, member_id)
            except ValueError:
                print("❌ Invalid member ID")
        
        elif choice == '4':
            client.read_card()
        
        elif choice == '5':
            client.check_nfc_status()
        
        elif choice == '6':
            # Complete workflow
            print("\n🔄 Complete NFC Card Assignment Workflow")
            print("-" * 40)
            
            # Step 1: Search member
            query = input("1. Enter search query to find member: ").strip()
            if not query:
                continue
            
            client.search_members(query, limit=5)
            
            # Step 2: Select member and generate token
            try:
                member_id = int(input("2. Enter member ID to generate token for: ").strip())
                expires = input("3. Expires in days (press Enter for no expiration): ").strip()
                expires_days = int(expires) if expires else None
                
                token = client.generate_token(member_id, expires_days)
                if not token:
                    continue
                
                # Step 3: Write to card
                proceed = input("4. Ready to write to NFC card? (y/n): ").strip().lower()
                if proceed == 'y':
                    client.write_token_to_card(token, member_id)
                    
            except ValueError:
                print("❌ Invalid input")
        
        elif choice == '7':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option. Please select 1-7.")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Gym NFC Management System CLI")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="API base URL (default: http://localhost:8000)")
    parser.add_argument("--username", help="Username for authentication")
    parser.add_argument("--password", help="Password for authentication")
    
    # Commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for members')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=10, help='Result limit')
    
    # Generate token command
    token_parser = subparsers.add_parser('generate', help='Generate token for member')
    token_parser.add_argument('member_id', type=int, help='Member ID')
    token_parser.add_argument('--expires', type=int, help='Expires in days')
    
    # Write command
    write_parser = subparsers.add_parser('write', help='Write token to NFC card')
    write_parser.add_argument('token', help='Token to write')
    write_parser.add_argument('member_id', type=int, help='Member ID')
    
    # Status command
    subparsers.add_parser('status', help='Check NFC reader status')
    
    # Read command
    subparsers.add_parser('read', help='Read data from NFC card')
    
    # Interactive command
    subparsers.add_parser('interactive', help='Start interactive mode')
    
    args = parser.parse_args()
    
    # Create client
    client = GymNFCClient(args.url)
    
    # Handle authentication
    if args.username and args.password:
        if not client.login(args.username, args.password):
            sys.exit(1)
    elif args.command and args.command != 'interactive':
        print("Error: Username and password required for non-interactive commands")
        sys.exit(1)
    
    # Execute commands
    if not args.command or args.command == 'interactive':
        interactive_mode(client)
    
    elif args.command == 'search':
        client.search_members(args.query, args.limit)
    
    elif args.command == 'generate':
        client.generate_token(args.member_id, args.expires)
    
    elif args.command == 'write':
        client.write_token_to_card(args.token, args.member_id)
    
    elif args.command == 'status':
        client.check_nfc_status()
    
    elif args.command == 'read':
        client.read_card()


if __name__ == "__main__":
    main()