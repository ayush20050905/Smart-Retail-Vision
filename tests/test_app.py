from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_demo_and_all_navigation():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=40)
    assert not app.exception
    assert len(app.metric)==4
    for mode in ['Analyze video','Saved runs','Tableau guide']:
        app.sidebar.radio[0].set_value(mode).run(timeout=40)
        assert not app.exception
