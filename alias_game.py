import streamlit as st
import random
import time
from typing import List
from dataclasses import dataclass
from enum import Enum

class Difficulty(Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

@dataclass
class Team:
    name: str
    score: int = 0
    
@dataclass
class GameState:
    teams: List[Team]
    current_team_index: int
    current_word: str
    guessed_words: List[str]
    round_time: int
    round_start_time: float
    game_started: bool
    countdown_started: bool
    countdown_time: float
    difficulty: Difficulty

class AliasGame:
    def __init__(self):
        self.word_list = [
                "cat", "dog", "house", "car", "book", "tree", "sun", "moon", "water", "food",
                "happy", "sad", "big", "small", "red", "blue", "green", "yellow", "fast", "slow",
                "hot", "cold", "up", "down", "left", "right", "yes", "no", "good", "bad",
                "friend", "family", "school", "work", "play", "sleep", "eat", "drink", "walk", "run",
                "music", "dance", "sing", "laugh", "smile", "cry", "think", "know", "see", "hear",
                "adventure", "mystery", "journey", "discovery", "challenge", "opportunity", "creativity",
                "imagination", "technology", "innovation", "tradition", "culture", "celebration",
                "communication", "relationship", "experience", "knowledge", "education", "development",
                "environment", "sustainability", "responsibility", "leadership", "teamwork", "collaboration",
                "achievement", "success", "failure", "mistake", "learning", "improvement", "progress",
                "freedom", "independence", "choice", "decision", "consequence", "result", "outcome",
                "possibility", "potential", "future", "present", "past", "memory", "history", "story",
                "philosophy", "psychology", "sociology", "anthropology", "archaeology", "meteorology",
                "astronomy", "astrophysics", "quantum", "relativity", "consciousness", "subconscious",
                "unconscious", "meditation", "mindfulness", "enlightenment", "transcendence", "nirvana",
                "karma", "dharma", "zen", "tao", "yin", "yang", "chakra", "aura", "energy", "vibration",
                "frequency", "resonance", "harmony", "balance", "equilibrium", "symmetry", "asymmetry",
                "paradox", "contradiction", "irony", "sarcasm", "satire", "allegory", "metaphor", "simile",
                "analogy", "comparison", "contrast", "juxtaposition", "oxymoron", "euphemism", "hyperbole"
        ]
    
    def get_random_word(self, difficulty: Difficulty) -> str:
        """Get a random word from the specified difficulty level."""
        words = self.word_list
        return random.choice(words)
    
    def initialize_game(self, team_names: List[str], difficulty: Difficulty, round_time: int) -> GameState:
        """Initialize a new game with teams and settings."""
        teams = [Team(name=name) for name in team_names]
        return GameState(
            teams=teams,
            current_team_index=0,
            current_word="",
            guessed_words=[],
            round_time=round_time,
            round_start_time=0,
            game_started=False,
            countdown_started=False,
            countdown_time=0,
            difficulty=difficulty
        )
    
    def start_countdown(self, game_state: GameState) -> GameState:
        """Start the 3-2-1 countdown before the round begins."""
        game_state.countdown_started = True
        game_state.countdown_time = time.time()
        return game_state
    
    def start_round(self, game_state: GameState) -> GameState:
        """Start a new round for the current team after countdown."""
        game_state.current_word = self.get_random_word(game_state.difficulty)
        game_state.guessed_words = []
        game_state.round_start_time = time.time()
        game_state.game_started = True
        game_state.countdown_started = False
        return game_state
    
    def success_word(self, game_state: GameState) -> GameState:
        """Mark current word as successfully guessed."""
        game_state.guessed_words.append(game_state.current_word)
        game_state.teams[game_state.current_team_index].score += 1
        game_state.current_word = self.get_random_word(game_state.difficulty)
        return game_state
    
    def skip_word(self, game_state: GameState) -> GameState:
        """Skip the current word and get a new one."""
        game_state.current_word = self.get_random_word(game_state.difficulty)
        return game_state
    
    def enemy_guessed(self, game_state: GameState) -> GameState:
        """Give point to enemy team when time runs out."""
        # Give point to the next team (enemy)
        enemy_index = (game_state.current_team_index + 1) % len(game_state.teams)
        game_state.teams[enemy_index].score += 1
        return game_state
    
    def end_round(self, game_state: GameState) -> GameState:
        """End the current round and switch to the next team."""
        game_state.current_team_index = (game_state.current_team_index + 1) % len(game_state.teams)
        game_state.game_started = False
        game_state.countdown_started = False
        return game_state
    
    def get_remaining_time(self, game_state: GameState) -> int:
        """Get the remaining time in the current round."""
        if not game_state.game_started:
            return game_state.round_time
        
        elapsed = time.time() - game_state.round_start_time
        remaining = max(0, game_state.round_time - int(elapsed))
        return remaining
    
    def is_round_finished(self, game_state: GameState) -> bool:
        """Check if the current round is finished (time's up)."""
        return self.get_remaining_time(game_state) == 0
    
    def get_countdown_number(self, game_state: GameState) -> int:
        """Get the current countdown number (3, 2, 1, or 0 if finished)."""
        if not game_state.countdown_started:
            return 0
        
        elapsed = time.time() - game_state.countdown_time
        countdown = max(0, 3 - int(elapsed))
        return countdown
    
    def is_countdown_finished(self, game_state: GameState) -> bool:
        """Check if countdown is finished."""
        return self.get_countdown_number(game_state) == 0 and game_state.countdown_started

def main():
    st.set_page_config(
        page_title="Alias Game",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 Alias Game")
    st.markdown("A word guessing game where teams try to guess words without using the word itself!")
    
    # Initialize session state
    if 'game' not in st.session_state:
        st.session_state.game = AliasGame()
    if 'game_state' not in st.session_state:
        st.session_state.game_state = None
    
    # Game setup
    if st.session_state.game_state is None:
        st.header("Game Setup")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Teams")
            num_teams = st.number_input("Number of teams", min_value=2, max_value=6, value=2)
            
            team_names = []
            for i in range(num_teams):
                name = st.text_input(f"Team {i+1} name", value=f"Team {i+1}", key=f"team_{i}")
                team_names.append(name)
        
        with col2:
            st.subheader("Game Settings")
            difficulty = st.selectbox(
                "Difficulty",
                options=[Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD]
            )

            print(difficulty)
            
            round_time = st.slider("Round time (seconds)", min_value=30, max_value=180, value=60)
        
        if st.button("Start Game", type="primary"):
            if len(set(team_names)) != len(team_names):
                st.error("Team names must be unique!")
            else:
                st.session_state.game_state = st.session_state.game.initialize_game(
                    team_names, difficulty, round_time
                )
                st.rerun()
    
    else:
        # Game interface
        game_state = st.session_state.game_state
        current_team = game_state.teams[game_state.current_team_index]
        
        # Header with team info and timer
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.subheader(f"Current Team: {current_team.name}")
            st.metric("Score", current_team.score)
        
        with col2:
            remaining_time = st.session_state.game.get_remaining_time(game_state)
            st.metric("Time Remaining", f"{remaining_time}s")
        
        with col3:
            if st.button("End Round"):
                st.session_state.game_state = st.session_state.game.end_round(game_state)
                st.rerun()
        
        # Game area
        if not game_state.game_started and not game_state.countdown_started:
            st.info("Click 'Start Round' to begin!")
            if st.button("Start Round", type="primary"):
                st.session_state.game_state = st.session_state.game.start_countdown(game_state)
                st.rerun()
        
        # Countdown phase
        elif game_state.countdown_started and not game_state.game_started:
            countdown_num = st.session_state.game.get_countdown_number(game_state)
            if countdown_num > 0:
                # Center the countdown
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.markdown(f"# {countdown_num}")
                    st.markdown("### Get ready to describe words!")
                time.sleep(1)
                st.rerun()
            else:
                # Countdown finished, start the round
                st.session_state.game_state = st.session_state.game.start_round(game_state)
                st.rerun()
        
        else:
            # Timer progress bar
            progress = (game_state.round_time - remaining_time) / game_state.round_time
            st.progress(progress)
            
            # Current word display
            st.markdown("---")
            st.markdown(f"### Current Word: **{game_state.current_word.upper()}**")
            st.markdown("---")
            
            # Action buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ SUCCESS", type="primary", use_container_width=True):
                    st.session_state.game_state = st.session_state.game.success_word(game_state)
                    st.rerun()
            
            with col2:
                if remaining_time > 0:
                    if st.button("⏭️ SKIP", use_container_width=True):
                        st.session_state.game_state = st.session_state.game.skip_word(game_state)
                        st.rerun()
                else:
                    st.warning("⏰ Time's up! Enemy gets a point if they guess this word.")
                    if st.button("👹 ENEMY GUESSED", type="secondary", use_container_width=True):
                        st.session_state.game_state = st.session_state.game.enemy_guessed(game_state)
                        st.rerun()
            
            # Guessed words display
            if game_state.guessed_words:
                st.markdown("### Successfully Guessed Words:")
                for word in game_state.guessed_words:
                    st.success(f"✓ {word}")
            
            # Auto-end round when time's up
            if st.session_state.game.is_round_finished(game_state):
                st.session_state.game_state = st.session_state.game.end_round(game_state)
                st.rerun()
        
        # Leaderboard
        st.markdown("---")
        st.subheader("Leaderboard")
        
        sorted_teams = sorted(game_state.teams, key=lambda x: x.score, reverse=True)
        for i, team in enumerate(sorted_teams):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "🏅"
            st.write(f"{medal} **{team.name}**: {team.score} points")
        
        # Reset game button
        if st.button("Reset Game"):
            st.session_state.game_state = None
            st.rerun()

if __name__ == "__main__":
    main()
