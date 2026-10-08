{
    'name': 'Service Report',
    'version': '1.0',
    'summary': 'Generate Service Report by Date Range',
    'category': 'Services',
    'author': 'Your Name',
    'depends': ['base', 'sale', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/wizard_views.xml',
        'report/report_actions.xml',
        'report/report_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}