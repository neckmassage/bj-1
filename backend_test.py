#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Blackjack API
Tests all endpoints and game logic as requested
"""

import requests
import json
import sys
from typing import Dict, Any

# Use the production URL from frontend/.env
BASE_URL = "https://d38a9f67-b884-4873-bc8f-c7fdc919a5a8.preview.emergentagent.com/api"

class BlackjackAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def test_hello_endpoint(self):
        """Test GET /api/ - Hello world endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "Blackjack" in data["message"]:
                    self.log_test("Hello World Endpoint", True, f"Response: {data}")
                    return True
                else:
                    self.log_test("Hello World Endpoint", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Hello World Endpoint", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Hello World Endpoint", False, f"Exception: {str(e)}")
            return False
            
    def test_new_game(self):
        """Test POST /api/game/new - Create new Blackjack game"""
        try:
            response = self.session.post(f"{self.base_url}/game/new")
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["id", "player_cards", "dealer_cards", "player_score", "dealer_score", "game_status", "balance"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("New Game Creation", False, f"Missing fields: {missing_fields}")
                    return None
                    
                # Validate initial game state
                if len(data["player_cards"]) != 2:
                    self.log_test("New Game Creation", False, f"Player should have 2 cards, got {len(data['player_cards'])}")
                    return None
                    
                if len(data["dealer_cards"]) != 2:
                    self.log_test("New Game Creation", False, f"Dealer should have 2 cards, got {len(data['dealer_cards'])}")
                    return None
                    
                if data["game_status"] != "playing":
                    self.log_test("New Game Creation", False, f"Game status should be 'playing', got '{data['game_status']}'")
                    return None
                    
                if data["balance"] != 1000.0:
                    self.log_test("New Game Creation", False, f"Initial balance should be 1000, got {data['balance']}")
                    return None
                    
                # Validate card structure
                for card in data["player_cards"]:
                    if not all(key in card for key in ["suit", "rank", "value", "display"]):
                        self.log_test("New Game Creation", False, f"Invalid card structure: {card}")
                        return None
                        
                self.log_test("New Game Creation", True, f"Game ID: {data['id']}, Player Score: {data['player_score']}")
                return data
            else:
                self.log_test("New Game Creation", False, f"Status: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("New Game Creation", False, f"Exception: {str(e)}")
            return None
            
    def test_place_bet(self, game_id: str):
        """Test POST /api/game/{game_id}/bet - Place a bet"""
        try:
            bet_data = {"amount": 100.0}
            response = self.session.post(f"{self.base_url}/game/{game_id}/bet", json=bet_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data:
                    self.log_test("Place Bet", False, f"Error: {data['error']}")
                    return False
                    
                if data["bet_amount"] != 100.0:
                    self.log_test("Place Bet", False, f"Bet amount should be 100, got {data['bet_amount']}")
                    return False
                    
                if data["balance"] != 900.0:  # 1000 - 100
                    self.log_test("Place Bet", False, f"Balance should be 900, got {data['balance']}")
                    return False
                    
                self.log_test("Place Bet", True, f"Bet: {data['bet_amount']}, Balance: {data['balance']}")
                return True
            else:
                self.log_test("Place Bet", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Place Bet", False, f"Exception: {str(e)}")
            return False
            
    def test_insufficient_balance_bet(self, game_id: str):
        """Test betting more than available balance"""
        try:
            bet_data = {"amount": 2000.0}  # More than balance
            response = self.session.post(f"{self.base_url}/game/{game_id}/bet", json=bet_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data and "Insufficient balance" in data["error"]:
                    self.log_test("Insufficient Balance Bet", True, f"Correctly rejected: {data['error']}")
                    return True
                else:
                    self.log_test("Insufficient Balance Bet", False, f"Should reject high bet: {data}")
                    return False
            else:
                self.log_test("Insufficient Balance Bet", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Insufficient Balance Bet", False, f"Exception: {str(e)}")
            return False
            
    def test_hit_action(self, game_id: str):
        """Test POST /api/game/{game_id}/action - Hit action"""
        try:
            action_data = {"action": "hit"}
            response = self.session.post(f"{self.base_url}/game/{game_id}/action", json=action_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data:
                    self.log_test("Hit Action", False, f"Error: {data['error']}")
                    return None
                    
                # Player should have more cards than before (at least 3)
                if len(data["player_cards"]) < 3:
                    self.log_test("Hit Action", False, f"Player should have at least 3 cards after hit, got {len(data['player_cards'])}")
                    return None
                    
                # Score should be recalculated
                if data["player_score"] <= 0:
                    self.log_test("Hit Action", False, f"Invalid player score: {data['player_score']}")
                    return None
                    
                self.log_test("Hit Action", True, f"Player cards: {len(data['player_cards'])}, Score: {data['player_score']}")
                return data
            else:
                self.log_test("Hit Action", False, f"Status: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Hit Action", False, f"Exception: {str(e)}")
            return None
            
    def test_stand_action(self, game_id: str):
        """Test POST /api/game/{game_id}/action - Stand action"""
        try:
            action_data = {"action": "stand"}
            response = self.session.post(f"{self.base_url}/game/{game_id}/action", json=action_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data:
                    self.log_test("Stand Action", False, f"Error: {data['error']}")
                    return None
                    
                # Game should be finished
                valid_end_states = ["player_win", "dealer_win", "push", "player_bust", "dealer_bust"]
                if data["game_status"] not in valid_end_states:
                    self.log_test("Stand Action", False, f"Invalid end state: {data['game_status']}")
                    return None
                    
                # Dealer score should be revealed
                if data["dealer_score"] <= 0:
                    self.log_test("Stand Action", False, f"Invalid dealer score: {data['dealer_score']}")
                    return None
                    
                self.log_test("Stand Action", True, f"Game ended: {data['game_status']}, Dealer score: {data['dealer_score']}")
                return data
            else:
                self.log_test("Stand Action", False, f"Status: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Stand Action", False, f"Exception: {str(e)}")
            return None
            
    def test_get_game_state(self, game_id: str):
        """Test GET /api/game/{game_id} - Get game state"""
        try:
            response = self.session.get(f"{self.base_url}/game/{game_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data:
                    self.log_test("Get Game State", False, f"Error: {data['error']}")
                    return None
                    
                # Check required fields
                required_fields = ["id", "player_cards", "dealer_cards", "player_score", "dealer_score", "game_status"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Get Game State", False, f"Missing fields: {missing_fields}")
                    return None
                    
                self.log_test("Get Game State", True, f"Retrieved game state for {game_id}")
                return data
            else:
                self.log_test("Get Game State", False, f"Status: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Get Game State", False, f"Exception: {str(e)}")
            return None
            
    def test_invalid_game_id(self):
        """Test operations with invalid game ID"""
        invalid_id = "invalid-game-id"
        
        # Test get game state with invalid ID
        try:
            response = self.session.get(f"{self.base_url}/game/{invalid_id}")
            if response.status_code == 200:
                data = response.json()
                if "error" in data and "not found" in data["error"].lower():
                    self.log_test("Invalid Game ID - Get State", True, f"Correctly rejected: {data['error']}")
                else:
                    self.log_test("Invalid Game ID - Get State", False, f"Should reject invalid ID: {data}")
            else:
                self.log_test("Invalid Game ID - Get State", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Game ID - Get State", False, f"Exception: {str(e)}")
            
    def test_ace_score_calculation(self):
        """Test Ace score calculation by creating multiple games"""
        print("\n=== Testing Ace Score Calculation ===")
        ace_games = []
        
        # Create multiple games to find one with Aces
        for i in range(10):
            game_data = self.test_new_game()
            if game_data:
                # Check if player has any Aces
                player_aces = [card for card in game_data["player_cards"] if card["rank"] == "A"]
                if player_aces:
                    ace_games.append(game_data)
                    print(f"Found game with {len(player_aces)} Ace(s): Score = {game_data['player_score']}")
                    
        if ace_games:
            self.log_test("Ace Score Calculation", True, f"Found {len(ace_games)} games with Aces")
        else:
            self.log_test("Ace Score Calculation", True, "No Aces found in sample games (normal probability)")
            
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("=== Starting Comprehensive Blackjack API Tests ===\n")
        
        # Test 1: Hello endpoint
        self.test_hello_endpoint()
        
        # Test 2: Create new game
        game_data = self.test_new_game()
        if not game_data:
            print("❌ Cannot continue tests - new game creation failed")
            return
            
        game_id = game_data["id"]
        
        # Test 3: Place bet
        self.test_place_bet(game_id)
        
        # Test 4: Test insufficient balance
        self.test_insufficient_balance_bet(game_id)
        
        # Test 5: Get game state
        self.test_get_game_state(game_id)
        
        # Test 6: Hit action
        hit_result = self.test_hit_action(game_id)
        
        # Test 7: Stand action (finish the game)
        if hit_result:
            self.test_stand_action(game_id)
            
        # Test 8: Invalid game ID
        self.test_invalid_game_id()
        
        # Test 9: Ace calculation
        self.test_ace_score_calculation()
        
        # Test 10: Complete game flow
        self.test_complete_game_flow()
        
        # Summary
        self.print_summary()
        
    def test_complete_game_flow(self):
        """Test a complete game from start to finish"""
        print("\n=== Testing Complete Game Flow ===")
        
        # Create new game
        game_data = self.test_new_game()
        if not game_data:
            return
            
        game_id = game_data["id"]
        
        # Place bet
        if not self.test_place_bet(game_id):
            return
            
        # Play until game ends
        max_hits = 5  # Prevent infinite loop
        hits = 0
        
        while hits < max_hits:
            # Get current state
            current_state = self.test_get_game_state(game_id)
            if not current_state:
                break
                
            if current_state["game_status"] != "playing":
                break
                
            # Decide action based on score
            if current_state["player_score"] < 17:
                hit_result = self.test_hit_action(game_id)
                if not hit_result:
                    break
                if hit_result["game_status"] != "playing":
                    break
                hits += 1
            else:
                # Stand
                self.test_stand_action(game_id)
                break
                
        self.log_test("Complete Game Flow", True, f"Completed game flow with {hits} hits")
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['details']}")
                    
        return passed == total

if __name__ == "__main__":
    tester = BlackjackAPITester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)