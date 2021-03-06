from uuid import UUID

import pytest
from taurus.entity.bounds.integer_bounds import IntegerBounds

from citrine.resources.material_run import MaterialRunCollection, MaterialRun
from tests.utils.session import FakeSession, FakeCall
from tests.utils.factories import MaterialRunFactory, MaterialRunDataFactory, LinkByUIDFactory


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> MaterialRunCollection:
    return MaterialRunCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
        session=session
    )


def test_register_material_run(collection, session):
    # Given
    session.set_response(MaterialRunDataFactory(name='Test MR 123'))
    material_run = MaterialRunFactory()

    # When
    registered = collection.register(material_run)

    # Then
    assert "<Material run 'Test MR 123'>" == str(registered)


def test_get_history(collection, session):
    # Given
    session.set_response({
        'context': 'Ignored',
        'root': MaterialRunDataFactory(name='Historic MR')
    })

    # When
    run = collection.get_history('id', '1234')

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='projects/{}/material-history/id/1234'.format(collection.project_id)
    )
    assert expected_call == session.last_call
    assert 'Historic MR' == run.name


def test_get_material_run(collection, session):
    # Given
    run_data = MaterialRunDataFactory(name='Cake 2')
    mr_id = run_data['uids']['id']
    session.set_response(run_data)

    # When
    run = collection.get(mr_id)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='projects/{}/datasets/{}/material-runs/id/{}'.format(collection.project_id, collection.dataset_id, mr_id)
    )
    assert expected_call == session.last_call
    assert 'Cake 2' == run.name


def test_list_material_runs(collection, session):
    # Given
    sample_run = MaterialRunDataFactory()
    session.set_response({
        'contents': [sample_run]
    })

    # When
    runs = collection.list(page=1, per_page=10)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='projects/{}/material-runs'.format(collection.project_id),
        params={
            'dataset_id': str(collection.dataset_id),
            'tags': [],
            'page': 1,
            'per_page': 10
        }
    )
    assert expected_call == session.last_call
    assert 1 == len(runs)
    assert sample_run['uids'] == runs[0].uids


def test_filter_by_tags(collection, session):
    # Given
    sample_run = MaterialRunDataFactory()
    session.set_response({
        'contents': [sample_run]
    })

    # When
    runs = collection.filter_by_tags(tags=["color"], page=1, per_page=10)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='projects/{}/material-runs'.format(collection.project_id),
        params={
            'dataset_id': str(collection.dataset_id),
            'tags': ["color"],
            'page': 1,
            'per_page': 10
        }
    )
    assert expected_call == session.last_call
    assert 1 == len(runs)
    assert sample_run['uids'] == runs[0].uids

    # When user gives a single string for tags, it should still work.
    collection.filter_by_tags(tags="color", page=1, per_page=10)

    # Then
    assert session.num_calls == 2
    assert session.last_call == expected_call

    # When user gives multiple tags, should raise NotImplemented Error
    with pytest.raises(NotImplementedError):
        collection.filter_by_tags(tags=["color", "shape"])


def test_filter_by_name(collection, session):
    # Given
    sample_run = MaterialRunDataFactory()
    session.set_response({'contents': [sample_run]})

    # When
    runs = collection.filter_by_name('test run', page=1, per_page=10)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='projects/{}/material-runs/filter-by-name'.format(collection.project_id),
        params={
            'dataset_id': str(collection.dataset_id),
            'name': 'test run',
            'exact': False,
            "page": 1,
            "per_page": 10
        }
    )
    assert expected_call == session.last_call
    assert 1 == len(runs)
    assert sample_run['uids'] == runs[0].uids


def test_filter_by_attribute_bounds(collection, session):
    # Given
    sample_run = MaterialRunDataFactory()
    session.set_response({'contents': [sample_run]})
    link = LinkByUIDFactory()
    bounds = {link: IntegerBounds(1, 5)}

    # When
    runs = collection.filter_by_attribute_bounds(bounds, page=1, per_page=10)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path='projects/{}/material-runs/filter-by-attribute-bounds'.format(collection.project_id),
        params={
            "page": 1,
            "per_page": 10,
            "dataset_id": str(collection.dataset_id)
        },
        json={
            'attribute_bounds': {
                link.id: {'lower_bound': 1, 'upper_bound': 5, 'type': 'integer_bounds'}
            }
        }
    )
    assert expected_call == session.last_call
    assert 1 == len(runs)
    assert sample_run['uids'] == runs[0].uids


def test_delete_material_run(collection, session):
    # Given
    material_run_uid = '2d3a782f-aee7-41db-853c-36bf4bff0626'
    material_run_scope = 'id'

    # When
    collection.delete(material_run_uid)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='DELETE',
        path='projects/{}/datasets/{}/material-runs/{}/{}'.format(
            collection.project_id,
            collection.dataset_id,
            material_run_scope,
            material_run_uid
        ),
    )
    assert expected_call == session.last_call


def test_build_discarded_objects_in_material_run():
    # Note:  This is really here just for test coverage - couldn't figure out how to
    #        get past the validation/serialization in MaterialRun.build - it might just be dead code
    material_run = MaterialRunFactory()
    material_run_data = MaterialRunDataFactory(
        name='Test Run',
        measurements=LinkByUIDFactory.create_batch(3)
    )

    MaterialRun._build_discarded_objects(material_run, material_run_data, None)


def test_material_run_cannot_register_with_no_id(collection):
    # Given
    collection.dataset_id = None

    # Then
    with pytest.raises(RuntimeError):
        collection.register(MaterialRunFactory())


def test_material_run_cannot_get_with_no_id(collection):
    # Given
    collection.dataset_id = None

    # Then
    with pytest.raises(RuntimeError):
        collection.get('123')


def test_material_run_filter_by_name_with_no_id(collection):
    # Given
    collection.dataset_id = None

    # Then
    with pytest.raises(RuntimeError):
        collection.filter_by_name('foo')
