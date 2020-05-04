"""Tests for citrine.informatics.reports serialization."""
import pytest
from copy import deepcopy

from citrine.informatics.descriptors import RealDescriptor
from citrine.informatics.reports import Report, ModelSummary, FeatureImportanceReport


def test_predictor_report_build(valid_predictor_report_data):
    """Build a predictor report and verify its structure."""
    report = Report.build(valid_predictor_report_data)

    assert report.status == 'OK'
    assert str(report.uid) == valid_predictor_report_data['id']

    x = RealDescriptor("x", 0, 1, "")
    y = RealDescriptor("y", 0, 100, "")
    z = RealDescriptor("z", 0, 101, "")
    assert report.descriptors == [x, y, z]

    lolo_model: ModelSummary = report.model_summaries[0]
    assert lolo_model.name == 'GeneralLoloModel_1'
    assert lolo_model.inputs == [x]
    assert lolo_model.outputs == [y]
    assert lolo_model.model_settings == {
        'Algorithm': 'Ensemble of non-linear estimators',
        'Number of estimators': 64,
        'Leaf model': 'Mean',
        'Use jackknife': True
    }
    assert lolo_model.feature_importances[0].dump() == FeatureImportanceReport('y', {'x': 1.0}).dump()

    exp_model: ModelSummary = report.model_summaries[1]
    assert exp_model.name == 'GeneralLosslessModel_2'
    assert exp_model.inputs == [x, y]
    assert exp_model.outputs == [z]
    assert exp_model.model_settings == {
        "Expression": "(z) <- (x + y)"
    }
    assert exp_model.feature_importances == []


def test_failed_predictor_report_build(valid_predictor_report_data):
    """Modify the predictor report to be invalid and check that the errors are caught."""
    too_many_descriptors = deepcopy(valid_predictor_report_data)
    # Multiple descriptors with the same key
    other_x = RealDescriptor("x", 0, 100, "")
    too_many_descriptors['report']['descriptors'].append(other_x.dump())
    with pytest.raises(RuntimeError):
        Report.build(too_many_descriptors)

    # A key that appears in inputs and/or outputs, but there is no corresponding descriptor.
    # This is done twice for coverage, once to catch a missing input and once for a missing output.
    too_few_descriptors = deepcopy(valid_predictor_report_data)
    too_few_descriptors['report']['descriptors'].pop()
    with pytest.raises(RuntimeError):
        Report.build(too_few_descriptors)
    too_few_descriptors['report']['descriptors'] = []
    with pytest.raises(RuntimeError):
        Report.build(too_few_descriptors)
