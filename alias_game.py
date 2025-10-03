import streamlit as st
import random
import time
import json
from typing import List
from dataclasses import dataclass
from streamlit.components.v1 import html

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
    max_points: int
    game_ended: bool = False
    winner: Team = None

def create_timer_html(seconds: int, timer_id: str = "timer") -> str:
    """Create HTML timer component for countdown in seconds."""
    return f"""
    <div id="{timer_id}" style="text-align: center; font-family: sans-serif;">
        <div style="font-size: 48px; font-weight: bold; color: #1f77b4; margin: 20px 0;">
            <span id="{timer_id}_seconds">{seconds:02d}</span>
        </div>
        <div style="font-size: 16px; color: #666;">שניות נותרו</div>
    </div>
    
    <script>
    function startTimer(timerId, duration) {{
        const timerElement = document.getElementById(timerId);
        const secondsSpan = document.getElementById(timerId + '_seconds');
        let hasBuzzed = false;

        function playBuzz() {{
            try {{
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();

                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);

                oscillator.type = 'square';
                oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                oscillator.frequency.exponentialRampToValueAtTime(200, audioContext.currentTime + 0.5);

                gainNode.gain.setValueAtTime(0.25, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.5);
            }} catch (e) {{
                console.log('Audio not supported');
            }}
        }}
        
        function updateTimer() {{
            const minutes = Math.floor(duration / 60);
            const seconds = duration % 60;
            
            secondsSpan.textContent = seconds.toString().padStart(2, '0');
            
            // Change color based on remaining time
            if (duration <= 10) {{
                secondsSpan.style.color = '#ff4444';
                timerElement.style.animation = 'pulse 0.5s infinite';
            }} else if (duration <= 30) {{
                secondsSpan.style.color = '#ff8800';
            }} else {{
                secondsSpan.style.color = '#1f77b4';
            }}
            
            if (duration <= 0) {{
                clearInterval(interval);
                secondsSpan.textContent = '00';
                secondsSpan.style.color = '#ff0000';
                timerElement.style.animation = 'none';
                if (!hasBuzzed) {{
                    hasBuzzed = true;
                    playBuzz();
                }}
            }}
            
            duration--;
        }}
        
        updateTimer(); // Initial call
        const interval = setInterval(updateTimer, 1000);
        
        // Return the interval ID so it can be cleared if needed
        return interval;
    }}
    
    // Start the timer when the component loads
    const timerInterval = startTimer('{timer_id}', {seconds});
    </script>
    
    <style>
    @keyframes pulse {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.05); }}
        100% {{ transform: scale(1); }}
    }}
    </style>
    """

class AliasGame:
    def __init__(self):
        # Load Hebrew words from JSON file
        try:
            with open('hebrew_words.json', 'r', encoding='utf-8') as f:
                self.word_list = json.load(f)
        except FileNotFoundError:
            st.error("Hebrew words file not found! Please make sure 'hebrew_words.json' is in the same directory.")
            self.word_list = ["שגיאה", "קובץ", "לא", "נמצא"]  # Fallback words
    
    def get_random_word(self) -> str:
        """Get a random word from the Hebrew word list."""
        return random.choice(self.word_list)
    
    def initialize_game(self, team_names: List[str], round_time: int, max_points: int) -> GameState:
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
            max_points=max_points
        )
    
    def start_countdown(self, game_state: GameState) -> GameState:
        """Start the 3-2-1 countdown before the round begins."""
        game_state.countdown_started = True
        game_state.countdown_time = time.time()
        return game_state
    
    def start_round(self, game_state: GameState) -> GameState:
        """Start a new round for the current team after countdown."""
        game_state.current_word = self.get_random_word()
        game_state.guessed_words = []
        game_state.round_start_time = time.time()
        game_state.game_started = True
        game_state.countdown_started = False
        return game_state
    
    def success_word(self, game_state: GameState) -> GameState:
        """Mark current word as successfully guessed."""
        game_state.guessed_words.append(game_state.current_word)
        game_state.teams[game_state.current_team_index].score += 1
        
        # Check for winner
        if game_state.teams[game_state.current_team_index].score >= game_state.max_points:
            game_state.game_ended = True
            game_state.winner = game_state.teams[game_state.current_team_index]
            game_state.game_started = False
        else:
            game_state.current_word = self.get_random_word()
        
        return game_state
    
    def skip_word(self, game_state: GameState) -> GameState:
        """Skip the current word and get a new one."""
        current_team = game_state.teams[game_state.current_team_index]
        current_team.score = max(0, current_team.score - 1)
        game_state.current_word = self.get_random_word()
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
        page_title="עליס - משחק מילים",
        page_icon="🎯",
        layout="wide"
    )
    st.markdown("""
    <style>
    html, body, [class*="css"], .stMarkdown, .stButton, .stMetric, .stAlert, .stSelectbox, .stTextInput {
        direction: rtl;
        text-align: right;
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, Helvetica, "Noto Sans", "Noto Sans Hebrew", sans-serif;
    }
    /* Keep sliders LTR so selection and thumb behave normally */
    .stSlider, .stSlider * { direction: ltr !important; text-align: left !important; }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🎯 עליס - משחק מילים")
    st.markdown("משחק ניחוש מילים בו הקבוצות מנסות לנחש מילים מבלי להשתמש במילה עצמה!")
    
    # Initialize session state
    if 'game' not in st.session_state:
        st.session_state.game = AliasGame()
    if 'game_state' not in st.session_state:
        st.session_state.game_state = None
    
    # Game setup
    if st.session_state.game_state is None:
        st.header("הגדרת משחק")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("קבוצות")
            num_teams = st.number_input("מספר קבוצות", min_value=2, max_value=6, value=2)
            
            team_names = []
            for i in range(num_teams):
                name = st.text_input(f"שם קבוצה {i+1}", value=f"קבוצה {i+1}", key=f"team_{i}")
                team_names.append(name)
        
        with col2:
            st.subheader("הגדרות משחק")
            round_time = st.slider("זמן סבב (בשניות)", min_value=30, max_value=180, value=60)
            max_points = st.number_input("נקודות לניצחון", min_value=5, max_value=100, value=20, help="הקבוצה הראשונה שתגיע לניקוד זה מנצחת!")
        
        if st.button("התחל משחק", type="primary"):
            if len(set(team_names)) != len(team_names):
                st.error("שמות הקבוצות חייבים להיות ייחודיים!")
            else:
                st.session_state.game_state = st.session_state.game.initialize_game(
                    team_names, round_time, max_points
                )
                st.rerun()
    
    else:
        # Game interface
        game_state = st.session_state.game_state
        current_team = game_state.teams[game_state.current_team_index]
        
        # Check if game has ended
        if game_state.game_ended and game_state.winner:
            st.balloons()
            st.success(f"🎉 **{game_state.winner.name}** wins with {game_state.winner.score} points! 🎉")
            st.markdown("---")
            
            # Show final leaderboard
            st.subheader("🏆 Final Results")
            sorted_teams = sorted(game_state.teams, key=lambda x: x.score, reverse=True)
            for i, team in enumerate(sorted_teams):
                if team == game_state.winner:
                    st.markdown(f"🥇 **{team.name}**: {team.score} points - **WINNER!**")
                else:
                    medal = "🥈" if i == 1 else "🥉" if i == 2 else "🏅"
                    st.markdown(f"{medal} **{team.name}**: {team.score} points")
            
            if st.button("🎮 New Game", type="primary"):
                st.session_state.game_state = None
                st.rerun()
            
            return
        
        # Header with team info and timer
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.subheader(f"קבוצה נוכחית: {current_team.name}")
            st.metric("ניקוד", current_team.score)
        
        with col2:
            remaining_time = st.session_state.game.get_remaining_time(game_state)
            
            # Use HTML timer for better performance
            if game_state.game_started:
                html(create_timer_html(remaining_time, "game_timer"), height=120)
                
                # Add warning messages
                if remaining_time <= 10 and remaining_time > 0:
                    st.warning("⏰ הזמן כמעט נגמר!")
                elif remaining_time == 0:
                    st.error("⏰ הזמן נגמר!")
                    # Play buzz sound when time runs out
                    st.markdown("""
                    <script>
                    // Simple beep sound using Web Audio API
                    function playBuzz() {
                        try {
                            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                            const oscillator = audioContext.createOscillator();
                            const gainNode = audioContext.createGain();
                            
                            oscillator.connect(gainNode);
                            gainNode.connect(audioContext.destination);
                            
                            // Create a descending buzz sound
                            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                            oscillator.frequency.exponentialRampToValueAtTime(200, audioContext.currentTime + 0.5);
                            
                            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
                            
                            oscillator.start(audioContext.currentTime);
                            oscillator.stop(audioContext.currentTime + 0.5);
                        } catch (e) {
                            console.log('Audio not supported');
                        }
                    }
                    
                    // Play the sound
                    playBuzz();
                    </script>
                    """, unsafe_allow_html=True)
            else:
                st.metric("זמן שנותר", f"{remaining_time}s")
        
        with col3:
            if st.button("סיום סבב"):
                st.session_state.game_state = st.session_state.game.end_round(game_state)
                st.rerun()
        
        # Game area
        if not game_state.game_started and not game_state.countdown_started:
            st.info("לחצו על 'התחל סבב' כדי להתחיל!")
            if st.button("התחל סבב", type="primary"):
                st.session_state.game_state = st.session_state.game.start_countdown(game_state)
                st.rerun()
        
        # Countdown phase
        elif game_state.countdown_started and not game_state.game_started:
            countdown_num = st.session_state.game.get_countdown_number(game_state)
            if countdown_num > 0:
                # Center the countdown using HTML
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    html(f"""
                    <div style="text-align: center; font-family: sans-serif;">
                        <div style="font-size: 72px; font-weight: bold; color: #1f77b4; margin: 20px 0;">
                            {countdown_num}
                        </div>
                        <div style="font-size: 24px; color: #666;">התכוננו לתאר מילים!</div>
                    </div>
                    """, height=150)
                time.sleep(1)
                st.rerun()
            else:
                # Countdown finished, start the round
                st.session_state.game_state = st.session_state.game.start_round(game_state)
                st.rerun()
        
        else:
            # Current word display
            st.markdown("---")
            st.markdown(f"### המילה הנוכחית: **{game_state.current_word.upper()}**")
            st.markdown("---")
            
            # Timer progress bar
            progress = (game_state.round_time - remaining_time) / game_state.round_time
            st.progress(progress)
            
            # Action buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ הצלחה", type="primary", use_container_width=True):
                    st.session_state.game_state = st.session_state.game.success_word(game_state)
                    st.rerun()
            
            with col2:
                if remaining_time > 0:
                    if st.button("⏭️ דלג", use_container_width=True):
                        st.session_state.game_state = st.session_state.game.skip_word(game_state)
                        st.rerun()
                else:
                    st.warning("⏰ הזמן נגמר! היריב יקבל נקודה אם ינחש את המילה.")
                    if st.button("👹 היריב ניחש", type="secondary", use_container_width=True):
                        st.session_state.game_state = st.session_state.game.enemy_guessed(game_state)
                        st.rerun()
            
            # Guessed words display
            if game_state.guessed_words:
                st.markdown("### מילים שניחשו בהצלחה:")
                for word in game_state.guessed_words:
                    st.success(f"✓ {word}")
            
            # Auto-end round when time's up
            if st.session_state.game.is_round_finished(game_state):
                st.session_state.game_state = st.session_state.game.end_round(game_state)
                st.rerun()
        
        # Leaderboard
        st.markdown("---")
        st.subheader(f"טבלת מובילים (ראשון ל-{game_state.max_points} נקודות מנצח!)")
        
        sorted_teams = sorted(game_state.teams, key=lambda x: x.score, reverse=True)
        for i, team in enumerate(sorted_teams):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "🏅"
            st.progress(team.score / game_state.max_points)
            st.write(f"{medal} **{team.name}**: {team.score}/{game_state.max_points} נקודות")
        
        # Reset game button
        if st.button("איפוס משחק"):
            st.session_state.game_state = None
            st.rerun()

if __name__ == "__main__":
    main()
