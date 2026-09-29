import json
from django.views.generic import TemplateView
from django.http import JsonResponse


class DictReportView(TemplateView):
    """
    Prototype implementation of DictReportView:
    Renders a preformed report dictionary at a URL endpoint.
    - Default GET: renders HTML embedding payload directly via json_script.
    - GET with ?format=json or Accept: application/json: returns pure JSON.
    - Integrators can supply report_dict directly or override get_report_dict(request).
    """
    template_name = 'reportcraft/report.html'
    report_dict: dict | None = None

    def get_report_dict(self, request=None) -> dict:
        if callable(self.report_dict):
            return self.report_dict()
        elif self.report_dict is not None:
            return self.report_dict
        return {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payload = self.get_report_dict(self.request)
        context['report'] = {
            'title': payload.get('title', 'Report'),
            'description': payload.get('description', ''),
            'theme': payload.get('theme', 'default'),
            'notes': payload.get('notes', ''),
        }
        context['payload'] = payload
        context['query'] = ''
        return context

    def get(self, request, *args, **kwargs):
        format_param = request.GET.get('format', '').lower()
        accept_header = request.headers.get('Accept', '')
        if format_param == 'json' or 'application/json' in accept_header:
            return JsonResponse(self.get_report_dict(request), safe=False)
        return super().get(request, *args, **kwargs)


PROTOTYPE_REPORT_DICT = {
    'title': 'Executive Leadership KPI Overview',
    'description': 'A preformed dictionary report rendered directly at a custom URL endpoint without database storage.',
    'theme': 'sketch',
    'sections': [
        {
            'title': 'High-Level Metrics',
            'style': 'row',
            'theme': 'sketch',
            'notes': 'Rendered via inline JSON embedding in a single HTTP request.',
            'content': [
                {
                    'title': 'Active Research Projects',
                    'kind': 'richtext',
                    'style': 'col-md-4',
                    'text': '## 142\n*+12% from last quarter*',
                    'description': 'Active cross-institutional grants',
                },
                {
                    'title': 'Publications (2026 YTD)',
                    'kind': 'richtext',
                    'style': 'col-md-4',
                    'text': '## 384\n*89 in top-tier venues*',
                    'description': 'Peer-reviewed outputs',
                },
                {
                    'title': 'Open Collaborations',
                    'kind': 'richtext',
                    'style': 'col-md-4',
                    'text': '## 27\n*Across 14 countries*',
                    'description': 'Global research partners',
                },
                {
                    'title': 'Outputs by Domain & Quarter',
                    'kind': 'table',
                    'style': 'col-md-6',
                    'header': 'column row',
                    'description': 'Publications broken down by subject category',
                    'notes': 'Quarterly snapshot from institutional warehouse',
                    'data': [
                        [
                            ['Domain', 'Q1', 'Q2', 'Q3', 'Q4'],
                            ['Computer Science', 45, 52, 60, 68],
                            ['Biomedical Sciences', 38, 42, 49, 55],
                            ['Physical Sciences', 22, 28, 31, 35],
                            ['Social Sciences', 15, 18, 20, 24],
                        ]
                    ],
                },
                {
                    'title': 'Quarterly Output Trends',
                    'kind': 'bars',
                    'style': 'col-md-6',
                    'description': 'Subject output distribution',
                    'scheme': 'Live8',
                    'y': 'Domain',
                    'x': 'Outputs',
                    'data': [
                        {'Domain': 'Computer Science', 'Outputs': 225},
                        {'Domain': 'Biomedical Sciences', 'Outputs': 184},
                        {'Domain': 'Physical Sciences', 'Outputs': 116},
                        {'Domain': 'Social Sciences', 'Outputs': 77},
                    ],
                    'categories': 'Domain',
                    'values': ['Outputs'],
                }
            ]
        }
    ]
}


class PrototypeDictReport(DictReportView):
    report_dict = PROTOTYPE_REPORT_DICT
