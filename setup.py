from setuptools import setup

requirements = [
    'PySide2', 'pyserial',
    'pyzmq', 'peakutils', 'numpy', 'pandas', 'appdirs', 'pint', 'psutil'
]

setup(
    name='Juice_SCM_GSE',
    version='0.0.1',
    description="Juice_SCM_GSE",
    author="Alexis Jeandet",
    author_email='alexis.jeandet@member.fsf.org',
    url='https://github.com/jeandet/Juice_SCM_GSE',
    packages=['juice_scm_gse', 'juice_scm_gse.gui', 'juice_scm_gse.utils', 'juice_scm_gse.config', 'juice_scm_gse.analysis', 'juice_scm_gse.arduino_monitor', 'juice_scm_gse.discovery_driver'],
#    package_data={'juice_scm_gse.images': ['*.png']},
    data_files=[
        ('share/icons/hicolor/scalable/apps', ['juice-scm-egse.svg'])
      ],
    entry_points={
        'console_scripts': [
            'Juice_SCM_GSE=juice_scm_gse.app:main',
            'Juice_Ardiuno_Monitor=juice_scm_gse.arduino_monitor:main',
            'Juice_Discovery_Driver=juice_scm_gse.discovery_driver:main'
        ]
    },
    install_requires=requirements,
    zip_safe=False,
    keywords='Juice_SCM_GSE',
    classifiers=[
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
