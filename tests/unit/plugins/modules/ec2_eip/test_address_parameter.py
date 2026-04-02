# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_eip


@pytest.fixture(name="mock_client")
def fixture_mock_client():
    """Create a mock EC2 client"""
    client = MagicMock()
    return client


def test_allocate_address_with_specific_ip(mock_client):
    """Test that address parameter is passed to allocate_ip_address"""
    with patch("ansible_collections.amazon.aws.plugins.modules.ec2_eip.allocate_ip_address") as mock_allocate:
        mock_allocate.return_value = {"PublicIp": "203.0.113.42", "AllocationId": "eipalloc-12345"}

        result, changed = ec2_eip.allocate_address(
            client=mock_client,
            check_mode=False,
            search_tags=None,
            domain="vpc",
            reuse_existing_ip_allowed=False,
            tags=None,
            public_ipv4_pool="ipv4pool-ec2-test123",
            address="203.0.113.42",
        )

        # Verify allocate_ip_address was called with Address parameter
        mock_allocate.assert_called_once()
        call_kwargs = mock_allocate.call_args[1]
        assert call_kwargs["Domain"] == "vpc"
        assert call_kwargs["PublicIpv4Pool"] == "ipv4pool-ec2-test123"
        assert call_kwargs["Address"] == "203.0.113.42"
        assert changed is True


def test_allocate_address_without_specific_ip(mock_client):
    """Test that address parameter is not passed when not provided"""
    with patch("ansible_collections.amazon.aws.plugins.modules.ec2_eip.allocate_ip_address") as mock_allocate:
        mock_allocate.return_value = {"PublicIp": "203.0.113.99", "AllocationId": "eipalloc-67890"}

        result, changed = ec2_eip.allocate_address(
            client=mock_client,
            check_mode=False,
            search_tags=None,
            domain="vpc",
            reuse_existing_ip_allowed=False,
            tags=None,
            public_ipv4_pool="ipv4pool-ec2-test123",
            address=None,
        )

        # Verify allocate_ip_address was called without Address parameter
        mock_allocate.assert_called_once()
        call_kwargs = mock_allocate.call_args[1]
        assert call_kwargs["Domain"] == "vpc"
        assert call_kwargs["PublicIpv4Pool"] == "ipv4pool-ec2-test123"
        assert "Address" not in call_kwargs
        assert changed is True


def test_allocate_address_check_mode_with_specific_ip(mock_client):
    """Test that no allocation happens in check mode"""
    with patch("ansible_collections.amazon.aws.plugins.modules.ec2_eip.allocate_ip_address") as mock_allocate:
        result, changed = ec2_eip.allocate_address(
            client=mock_client,
            check_mode=True,
            search_tags=None,
            domain="vpc",
            reuse_existing_ip_allowed=False,
            tags=None,
            public_ipv4_pool="ipv4pool-ec2-test123",
            address="203.0.113.42",
        )

        # Verify allocate_ip_address was NOT called in check mode
        mock_allocate.assert_not_called()
        assert result is None
        assert changed is True


def test_allocate_address_with_pool_but_no_address(mock_client):
    """Test allocating from pool without specifying address (random selection)"""
    with patch("ansible_collections.amazon.aws.plugins.modules.ec2_eip.allocate_ip_address") as mock_allocate:
        mock_allocate.return_value = {"PublicIp": "203.0.113.99", "AllocationId": "eipalloc-random"}

        result, changed = ec2_eip.allocate_address(
            client=mock_client,
            check_mode=False,
            search_tags=None,
            domain="vpc",
            reuse_existing_ip_allowed=False,
            tags=None,
            public_ipv4_pool="ipv4pool-ec2-test123",
            address=None,
        )

        # Verify allocate_ip_address was called with pool but no address
        mock_allocate.assert_called_once()
        call_kwargs = mock_allocate.call_args[1]
        assert call_kwargs["PublicIpv4Pool"] == "ipv4pool-ec2-test123"
        assert "Address" not in call_kwargs
        assert changed is True
