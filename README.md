FakeRoBERT
==============================

This project consists in a trained model that predict credibility scores of news that is integrated in a web server.

Project Organization

------------
```bash
├── cluster
│   ├── charts                           - Kubernetes deployment
│   │   ├── app-infra
│   │   ├── app-logic
│   │   ├── celery-beat-chart
│   │   ├── celery-scrapper-chart
│   │   ├── config.yaml
│   │   ├── docker_mgr.sh
│   │   ├── imgs.docker.json
│   │   ├── infra_env.yaml
│   │   ├── init.sh
│   │   ├── internet_env.yaml
│   │   ├── k8s-infra
│   │   ├── local-path-provisioner-chart
│   │   ├── mgr_cfg.json
│   │   ├── mgr.py
│   │   ├── predicter-chart
│   │   └── tags.yaml
│   ├── configs                         - Microservices configurations
│   ├── dashboards                      - Grafana dashboards
│   ├── docker                          - Docker images
│   │   ├── celery-beat
│   │   ├── celery-scrapper
│   │   └── predicter
│   └── fakepred                        - Microservices sources
│       ├── celery
│       ├── celery_beat
│       ├── celery_scrapper
│       ├── mongodb
│       ├── predicter
│       ├── redis
│       ├── scrapper
│       └── utils
├── data                                - Data for models
│   ├── external
│   ├── interim
│   ├── processed
│   └── raw
│       ├── official-ro.csv
│       ├── Raw_Dataset.csv
│       └── scrapped_data
│           ├── celery_scrapped_data
│           ├── guv.ro
│           ├── klausiohannis
│           ├── mae.romania
│           ├── mapn.ro
│           ├── ministeruldeinterne
│           ├── MinisterulSanatatii
│           └── timesnewroman
├── docs                                - Documents
│   ├── articles
│   ├── commands.rst
│   ├── conf.py
│   ├── getting-started.rst
│   ├── index.rst
│   ├── make.bat
│   ├── Makefile
│   ├── mockup
│   └── PROJECT_VISION.md
├── geckodriver.log
├── LICENSE
├── licenta-env
├── Makefile
├── models
├── mypy.ini
├── notebooks
├── README.md
├── references
├── reports
│   └── figures
├── requirements.txt
├── setup.py
├── src                                 - Model processing sources
│   ├── cleaner
│   ├── data
│   ├── features
│   ├── models
│   └── visualization
├── src.egg-info
├── target
├── visualization                       - Output from data exploring
├── test_environment.py
└── tox.ini
```
--------

If you need to find something in this repository, consult the filesystem above.

You need to install a python virtual environment with `Python 3.10` version.

Install requirements(root file `requirements.txt` and also `requirements.txt` files from `cluster` directory) in installed venv.

To deploy this repository you need technologies like:
- minikube
- helm
- helmfile
- k8s lens
