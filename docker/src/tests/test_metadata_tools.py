from tools.metadata_tools import get_workspaces_list
import pytest

@pytest.mark.parametrize("include_shared_workspaces, contains_str, expected", [
    (False, 'Bugs Tracker Dataset', [{'workspaceId': '2588359000000656130', 'workspaceName': 'Bugs Tracker Dataset - Source', 'workspaceDesc': '', 'orgId': '784783856', 'createdTime': '1750049600716', 'createdBy': 'ashwinprasad.h@zohocorp.com', 'isDefault': False, 'owned': True}])
])
def test_get_workspaces(include_shared_workspaces, contains_str, expected):
    response = get_workspaces_list(include_shared_workspaces=include_shared_workspaces, contains_str=contains_str)
    print(response)
    assert response == expected