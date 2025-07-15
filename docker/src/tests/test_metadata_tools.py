from tools.metadata_tools import get_workspaces_list, get_view_list
import pytest

@pytest.mark.parametrize("include_shared_workspaces, contains_str, expected", [
    (False, 'Bugs Tracker Dataset', [{'workspaceName': 'Bugs Tracker Dataset - Source', 'workspaceDesc': '', 'isDefault': False, 'owned': True}])
])
def test_get_workspaces(include_shared_workspaces, contains_str, expected):
    response = get_workspaces_list(include_shared_workspaces=include_shared_workspaces, contains_str=contains_str)
    response.pop('orgId')
    response.pop('createdBy')
    response.pop('createdTime')
    response.pop('workspaceId')
    assert response == expected


def test_get_viewlist():
    pass