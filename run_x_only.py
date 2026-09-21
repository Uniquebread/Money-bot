"""
Thin entrypoint used by .github/workflows/x-digest.yml. Runs the full
pipeline but with the free RSS sources turned off, since those already get
their own run every 2 hours via digest.yml - this workflow exists purely to
run the paid X source on its own, deliberately slower, schedule.
"""
import main as bot_main

if __name__ == "__main__":
    bot_main.FREE_SOURCES = []
    bot_main.run()
