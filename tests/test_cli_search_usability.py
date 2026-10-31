"""First-time-user experience of the search screen (NFR-02)."""
DAY = "2026-11-02"          # a Monday; CLI "today" is 2026-10-24 (Saturday)


def test_station_list_is_shown_before_asking_anything(run_cli):
    out = run_cli(["4", "Bengaluru", "Delhi", DAY, "0"])
    assert "Stations: Bengaluru, Delhi, Mysuru" in out
    assert out.index("Stations:") < out.index("train(s) found")


def test_today_and_tomorrow_are_accepted(run_cli):
    assert "train(s) found on 2026-10-24" in run_cli(["4", "Bengaluru", "Delhi", "today", "0"])
    assert "train(s) found on 2026-10-25" in run_cli(["4", "Bengaluru", "Delhi", "tomorrow", "0"])


def test_misspelt_station_gets_did_you_mean(run_cli):
    out = run_cli(["4", "Dehli", "Bengaluru", DAY, "0"])
    assert "Error: Unknown station: Dehli. Did you mean: Delhi?" in out


def test_second_station_typo_is_the_one_suggested(run_cli):
    out = run_cli(["4", "Bengaluru", "Mysoor", DAY, "0"])
    assert "Unknown station: Mysoor. Did you mean: Mysuru?" in out


def test_unknown_station_with_no_close_match_points_to_the_list(run_cli):
    out = run_cli(["4", "Atlantis", "Delhi", DAY, "0"])
    assert "Error: Unknown station: Atlantis. Pick a station from the list above." in out


def test_empty_result_explains_what_to_do_next(run_cli):
    out = run_cli(["4", "Mysuru", "Delhi", DAY, "0"])
    assert "No trains found for that route and date." in out
    assert "No trains leave from Mysuru." in out


def test_results_tell_the_user_how_to_book(run_cli):
    assert "choose option 6" in run_cli(["4", "Bengaluru", "Delhi", DAY, "0"])


def test_date_prompt_mentions_today_and_tomorrow(cli_conn):
    from datetime import date, datetime
    from railway.cli import App
    prompts = []
    feed = iter(["4", "Bengaluru", "Delhi", DAY, "0"])
    App(cli_conn, ask=lambda p: prompts.append(p) or next(feed), say=lambda m: None,
        today=date(2026, 10, 24), now=datetime(2026, 10, 24, 10, 0)).run()
    assert any("today" in p and "tomorrow" in p for p in prompts)