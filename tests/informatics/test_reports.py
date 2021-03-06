"""Tests reports initialization."""
from citrine.informatics.reports import PredictorReport


def test_report_init():
    """Tests that a Report object can be constructed."""
    report = PredictorReport('ERROR', dict(key='val'))
    assert report.status == 'ERROR'
    assert report.json['key'] == 'val'
