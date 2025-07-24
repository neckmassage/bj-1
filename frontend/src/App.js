import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BlackjackGame = () => {
  const [gameState, setGameState] = useState(null);
  const [gameId, setGameId] = useState(null);
  const [betAmount, setBetAmount] = useState(1);
  const [isAnimating, setIsAnimating] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [balance, setBalance] = useState(1000);
  const [isDistributing, setIsDistributing] = useState(false);
  const [dealingOrder, setDealingOrder] = useState([]);
  const [visibleCards, setVisibleCards] = useState({ player: [], dealer: [] });
  const [editingBalance, setEditingBalance] = useState(false);

  // Simulate realistic card distribution
  const distributeCards = (cards, dealerCards) => {
    setIsDistributing(true);
    setVisibleCards({ player: [], dealer: [] });
    
    // Casino order: player, dealer, player, dealer
    const distributionOrder = [
      { target: 'player', cardIndex: 0 },
      { target: 'dealer', cardIndex: 0 },
      { target: 'player', cardIndex: 1 },
      { target: 'dealer', cardIndex: 1 }
    ];
    
    setDealingOrder(distributionOrder);
    
    distributionOrder.forEach((deal, index) => {
      setTimeout(() => {
        setVisibleCards(prev => {
          const newVisible = { ...prev };
          if (deal.target === 'player') {
            newVisible.player = [...newVisible.player, cards[deal.cardIndex]];
          } else {
            // Dealer's second card stays hidden during game
            const card = dealerCards[deal.cardIndex];
            const isHidden = deal.cardIndex === 1;
            newVisible.dealer = [...newVisible.dealer, { ...card, isHidden }];
          }
          return newVisible;
        });
        
        // End distribution after last card
        if (index === distributionOrder.length - 1) {
          setTimeout(() => {
            setIsDistributing(false);
          }, 300);
        }
      }, index * 400); // 400ms between each card
    });
  };

  // Start new game
  const startNewGame = async () => {
    try {
      const response = await axios.post(`${API}/game/new`);
      setGameState(response.data);
      setGameId(response.data.id);
      setBetAmount(1);
      setShowResult(false);
      
      // Start realistic card distribution
      distributeCards(response.data.player_cards, response.data.dealer_cards);
      
    } catch (error) {
      console.error("Error starting new game:", error);
    }
  };

  // Place bet
  const placeBet = async () => {
    if (!gameId) return;
    
    try {
      const response = await axios.post(`${API}/game/${gameId}/bet`, {
        amount: betAmount
      });
      setGameState(response.data);
      setBalance(response.data.balance);
    } catch (error) {
      console.error("Error placing bet:", error);
    }
  };

  // Tirer (Hit) action
  const tirer = async () => {
    if (!gameId || isAnimating || isDistributing) return;
    
    setIsAnimating(true);
    
    try {
      const response = await axios.post(`${API}/game/${gameId}/action`, {
        action: "hit"
      });
      
      // Animate new card from deck
      setTimeout(() => {
        const newCard = response.data.player_cards[response.data.player_cards.length - 1];
        setVisibleCards(prev => ({
          ...prev,
          player: [...prev.player, newCard]
        }));
        
        setTimeout(() => {
          setGameState(response.data);
          setBalance(response.data.balance);
          setIsAnimating(false);
          
          // Show result if game ended (but only after seeing the card)
          if (response.data.game_status !== "playing") {
            setTimeout(() => setShowResult(true), 800);
          }
        }, 200);
      }, 300);
      
    } catch (error) {
      console.error("Error hitting:", error);
      setIsAnimating(false);
    }
  };

  // Rester (Stand) action
  const rester = async () => {
    if (!gameId || isAnimating || isDistributing) return;
    
    setIsAnimating(true);
    
    try {
      const response = await axios.post(`${API}/game/${gameId}/action`, {
        action: "stand"
      });
      
      // First reveal dealer's hidden card
      setTimeout(() => {
        setVisibleCards(prev => ({
          ...prev,
          dealer: prev.dealer.map((card, index) => 
            index === 1 ? { ...card, isHidden: false } : card
          )
        }));
        
        // Then add any additional dealer cards one by one
        const additionalCards = response.data.dealer_cards.slice(2);
        
        if (additionalCards.length > 0) {
          additionalCards.forEach((card, index) => {
            setTimeout(() => {
              setVisibleCards(prev => ({
                ...prev,
                dealer: [...prev.dealer, card]
              }));
            }, (index + 1) * 400);
          });
        }
        
        // Update game state and show result after all animations
        setTimeout(() => {
          setGameState(response.data);
          setBalance(response.data.balance);
          setIsAnimating(false);
          setTimeout(() => setShowResult(true), 600);
        }, additionalCards.length * 400 + 800);
        
      }, 500);
      
    } catch (error) {
      console.error("Error standing:", error);
      setIsAnimating(false);
    }
  };

  // Card component with realistic animations
  const Card = ({ card, isHidden = false, isDealer = false, index = 0, isWinning = false, isDistributing = false }) => {
    const getCardSymbol = (suit) => {
      const symbols = {
        hearts: "♥",
        diamonds: "♦", 
        clubs: "♣",
        spades: "♠"
      };
      return symbols[suit] || "";
    };

    const getCardColor = (suit) => {
      return suit === "hearts" || suit === "diamonds" ? "#E74C3C" : "#2C3E50";
    };

    if (isHidden || card?.isHidden) {
      return (
        <div 
          className={`card card-back ${isDistributing ? 'card-dealing' : ''}`}
          style={{ 
            animationDelay: `${index * 400}ms`,
            zIndex: 10 - index 
          }}
        >
          <div className="card-back-content">
            <div className="card-pattern"></div>
          </div>
        </div>
      );
    }

    return (
      <div 
        className={`card ${isDistributing ? 'card-dealing card-flipping' : ''} ${isWinning ? 'card-winning' : ''}`}
        style={{ 
          animationDelay: `${index * 400}ms`,
          zIndex: 10 - index,
          color: getCardColor(card.suit)
        }}
      >
        <div className="card-content">
          <div className="card-rank">{card.display}</div>
          <div className="card-suit">{getCardSymbol(card.suit)}</div>
        </div>
      </div>
    );
  };

  // Balance editor
  const handleBalanceEdit = (newBalance) => {
    const balance = parseFloat(newBalance);
    if (!isNaN(balance) && balance >= 0) {
      setBalance(balance);
    }
    setEditingBalance(false);
  };

  // Get game result message in French
  const getResultMessage = () => {
    if (!gameState || !showResult) return null;
    
    const { game_status, bet_amount } = gameState;
    
    switch (game_status) {
      case "player_win":
      case "dealer_bust":
        return { type: "win", text: `VOUS GAGNEZ +${bet_amount}€` };
      case "dealer_win":
      case "player_bust":
        return { type: "lose", text: `VOUS PERDEZ -${bet_amount}€` };
      case "push":
        return { type: "push", text: "ÉGALITÉ" };
      default:
        return null;
    }
  };

  const result = getResultMessage();
  const isWinning = result?.type === "win";

  useEffect(() => {
    startNewGame();
  }, []);

  if (!gameState) {
    return (
      <div className="blackjack-container">
        <div className="loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="blackjack-container">
      {/* Header */}
      <div className="header">
        <div className="stake-logo-header">
          <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTIwIDQwQzMxLjA0NTcgNDAgNDAgMzEuMDQ1NyA0MCAyMEM0MCA4Ljk1NDMgMzEuMDQ1NyAwIDIwIDBDOC45NTQzIDAgMCA4Ljk1NDMgMCAyMEMwIDMxLjA0NTcgOC45NTQzIDQwIDIwIDQwWiIgZmlsbD0iIzFCQzI3QSIvPgo8cGF0aCBkPSJNMTYuNSAyOC41VjE2LjVIMjMuNVYyOC41SDE2LjVaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4K" alt="Stake" />
          <span>Stake</span>
        </div>
        
        <div className={`balance ${isWinning && showResult ? 'balance-winning' : ''}`}>
          ${balance.toFixed(2)}
        </div>
        
        <div className="header-actions">
          <button className="wallet-btn">Wallet</button>
        </div>
      </div>

      {/* Game Info */}
      <div className="game-info">
        <div className="payout-info">BLACKJACK PAYS 3 TO 2</div>
        <div className="insurance-info">INSURANCE PAYS 2 TO 1</div>
      </div>

      {/* Game Area */}
      <div className="game-area">
        {/* Dealer Section */}
        <div className="dealer-section">
          <div className="section-label">
            <span>Dealer</span>
            <span className="score">{gameState.game_status === "playing" ? gameState.dealer_score : calculate_final_dealer_score()}</span>
          </div>
          <div className="cards-container">
            {gameState.dealer_cards.map((card, index) => (
              <Card 
                key={index}
                card={card}
                isHidden={index === 1 && gameState.game_status === "playing"}
                isDealer={true}
                index={index}
              />
            ))}
          </div>
        </div>

        {/* Player Section */}
        <div className="player-section">
          <div className="section-label">
            <span>Player</span>  
            <span className="score">{gameState.player_score}</span>
          </div>
          <div className="cards-container">
            {gameState.player_cards.map((card, index) => (
              <Card 
                key={index}
                card={card}
                index={index}
                isWinning={isWinning && showResult}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Result Banner */}
      {result && showResult && (
        <div className={`result-banner ${result.type}`}>
          {result.text}
        </div>
      )}

      {/* Betting Controls */}
      <div className="betting-controls">
        <div className="bet-amount">
          <label>Bet Amount</label>
          <div className="bet-input-container">
            <input 
              type="number" 
              value={betAmount} 
              onChange={(e) => setBetAmount(Number(e.target.value))}
              min="1"
              max={balance}
            />
            <div className="bet-buttons">
              <button onClick={() => setBetAmount(Math.max(1, betAmount + 1))}>+1</button>
              <button onClick={() => setBetAmount(Math.max(1, betAmount + 5))}>+5</button>
              <button onClick={() => setBetAmount(Math.max(1, betAmount + 25))}>+25</button>
              <button onClick={() => setBetAmount(Math.max(1, betAmount + 100))}>+100</button>
            </div>
          </div>
        </div>
      </div>

      {/* Game Controls */}
      <div className="game-controls">
        {gameState.game_status === "playing" ? (
          <>
            <button 
              className="control-btn hit-btn" 
              onClick={hit}
              disabled={isAnimating}
            >
              <span className="btn-icon">🔥</span>
              Hit
            </button>
            <button 
              className="control-btn stand-btn" 
              onClick={stand}
              disabled={isAnimating}
            >
              Stand
            </button>
          </>
        ) : (
          <button 
            className="control-btn deal-btn" 
            onClick={startNewGame}
          >
            New Game
          </button>
        )}
      </div>
    </div>
  );

  function calculate_final_dealer_score() {
    if (!gameState || gameState.game_status === "playing") return gameState?.dealer_score || 0;
    
    let score = 0;
    let aces = 0;
    
    for (let card of gameState.dealer_cards) {
      if (card.rank === 'A') {
        aces += 1;
        score += 11;
      } else {
        score += card.value;
      }
    }
    
    while (score > 21 && aces > 0) {
      score -= 10;
      aces -= 1;
    }
    
    return score;
  }
};

function App() {
  return (
    <div className="App">
      <BlackjackGame />
    </div>
  );
}

export default App;