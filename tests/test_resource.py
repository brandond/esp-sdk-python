import json
import mock

import esp
from .base import TestBase


class TestResource(TestBase):

    def setUp(self):
        self.report1 = {
            'id': '1',
            'type': 'reports',
            'attributes': {
                'status': 'completed',
                'created_at': '2016-02-26T18:00:00.000Z',
                'updated_at': '2016-02-26T18:03:48.000Z',
            },
            'relationships': {
                'alerts': {
                    'links': {
                        'related': 'http://localhost:3000/api/v2/reports/1/alerts.json'
                    }
                },
                'organization': {
                    'links': {
                        'related': 'http://localhost:3000/api/v2/reports/1/organization.json'
                    }
                },
                'sub_organization': {
                    'links': {
                        'related': 'http://localhost:3000/api/v2/reports/1/sub_organization.json'
                    }
                },
                'team': {
                    'links': {
                        'related': 'http://localhost:3000/api/v2/reports/1/team.json'
                    }
                },
            }
        }

        self.report2 = {
            'id': '2',
            'type': 'reports',
            'attributes': {
                'status': 'processing',
                'created_at': '2016-02-26T18:00:00.000Z',
                'updated_at': '2016-02-26T18:03:48.000Z',
            },
            'relationships': {
                'alerts': {
                    'links': {
                        'related': 'http://localhost:3000/api/v2/reports/2/alerts.json'
                    }
                },
                'organization': {
                    'links': {
                        'related': 'http://localhost:3000/api/v2/reports/2/organization.json'
                    }
                },
                'sub_organization': {
                    'links': {
                        'related': 'http://localhost:3000/api/v2/reports/2/sub_organization.json'
                    }
                },
                'team': {
                    'links': {
                        'related': 'http://localhost:3000/api/v2/reports/2/team.json'
                    }
                },
            }
        }

        self.report_response = json.dumps({'data': self.report1})
        self.reports_response = json.dumps({'data': [self.report1,
                                                     self.report2]})

        self.queued_report = {
            'id': '1',
            'type': 'reports',
            'attributes': {
                'status': 'queued',
                'created_at': '2016-02-26T18:00:00.000Z',
                'updated_at': '2016-02-26T18:03:48.000Z',
            },
            'relationships': {
                'alerts': {
                    'links': {
                        'related': 'http://localhost:3000/api/v2/reports/1/alerts.json'
                    }
                },
                'organization': {
                    'links': {
                        'related': 'http://localhost:3000/api/v2/reports/1/organization.json'
                    }
                },
                'sub_organization': {
                    'links': {
                        'related': 'http://localhost:3000/api/v2/reports/1/sub_organization.json'
                    }
                },
                'team': {
                    'links': {
                        'related': 'http://localhost:3000/api/v2/reports/1/team.json'
                    }
                },
            }
        }

        self.queued_report_response = json.dumps({'data': self.queued_report})

        super(TestResource, self).setUp()

    @mock.patch('esp.sdk.requests.get')
    def test_can_fetch_a_single_resource(self, mock_get):
        mock_response = mock.Mock()
        mock_response.json.return_value = json.loads(self.report_response)
        mock_get.return_value = mock_response

        report = esp.Report.find(id=1)

        self.assertIsInstance(report, esp.report.Report)
        self.assertEqual(report.status, 'completed')
        self.assertEqual(report.id_, '1')

    @mock.patch('esp.sdk.requests.get')
    def test_relationships_are_cachedrelationships(self, mock_get):
        mock_response = mock.Mock()
        mock_response.json.return_value = json.loads(self.report_response)
        mock_get.return_value = mock_response

        report = esp.Report.find(id=1)

        self.assertIsInstance(report._attributes['alerts'],
                              esp.resource.CachedRelationship)
        self.assertIsInstance(report._attributes['organization'],
                              esp.resource.CachedRelationship)
        self.assertIsInstance(report._attributes['sub_organization'],
                              esp.resource.CachedRelationship)
        self.assertIsInstance(report._attributes['team'],
                              esp.resource.CachedRelationship)

    @mock.patch('esp.sdk.requests.get')
    def test_can_fetch_a_collection(self, mock_get):
        mock_response = mock.Mock()
        mock_response.json.return_value = json.loads(self.reports_response)
        mock_get.return_value = mock_response
        reports = esp.Report.find()

        self.assertIsInstance(reports, esp.resource.PaginatedCollection)
        self.assertEqual(len(reports), 2)

    @mock.patch('esp.sdk.requests.post')
    def test_can_create_resources(self, mock_post):
        mock_response = mock.Mock()
        mock_response.json.return_value = json.loads(
            self.queued_report_response)
        mock_post.return_value = mock_response

        report = esp.Report.create(team_id=4)

        self.assertIsInstance(report, esp.report.Report)
        self.assertEqual(report.status, 'queued')
        payload = json.dumps({'data': {'type':
                                       'reports',
                                       'attributes': {'team_id': 4}}})
        self.assertEqual(mock_post.call_args[0],
                         ('http://localhost:3000/api/v2/reports',))
        self.assertEqual(mock_post.call_args[1]['data'],
                         payload)

    def test_resources_have_singular_and_plural_names(self):
        # just testing a few of these.
        self.assertEqual(esp.Report.singular_name, 'report')
        self.assertEqual(esp.Report.plural_name, 'reports')
        self.assertEqual(esp.ExternalAccount.singular_name, 'external_account')
        self.assertEqual(esp.ExternalAccount.plural_name, 'external_accounts')

    def test_resource_path(self):
        self.assertEqual(esp.Report._resource_path(1), 'reports/1')
        self.assertEqual(esp.ExternalAccount._resource_path(1), 'external_accounts/1')

    def test_resource_collection_path(self):
        self.assertEqual(esp.Report._resource_collection_path(), 'reports')
        self.assertEqual(esp.ExternalAccount._resource_collection_path(), 'external_accounts')

    def test_resource_collection_path_with_extra(self):
        self.assertEqual(
            esp.Report._resource_collection_path(extra=['foo', 'bar']),
            'reports/foo/bar')
        self.assertEqual(
            esp.ExternalAccount._resource_collection_path(extra=['foo', 'bar']),
            'external_accounts/foo/bar')

    def test_resource_path_with_extra(self):
        self.assertEqual(
            esp.Report._resource_path(1, extra=['foo', 'bar']),
            'reports/1/foo/bar')
        self.assertEqual(
            esp.ExternalAccount._resource_path(1, extra=['foo', 'bar']),
            'external_accounts/1/foo/bar')

    def test_resource_collection_path_with_querystring(self):
        self.assertEqual(
            esp.Report._resource_collection_path(
                querystring='testkey=testvalue&name=foo'),
            'reports?testkey=testvalue&name=foo')
        self.assertEqual(
            esp.ExternalAccount._resource_collection_path(
                querystring='testkey=testvalue&name=foo'),
            'external_accounts?testkey=testvalue&name=foo')

    def test_resource_path_with_querystring(self):
        self.assertEqual(
            esp.Report._resource_path(1,
                querystring='testkey=testvalue&name=foo'),
            'reports/1?testkey=testvalue&name=foo')
        self.assertEqual(
            esp.ExternalAccount._resource_path(1,
                querystring='testkey=testvalue&name=foo'),
            'external_accounts/1?testkey=testvalue&name=foo')
