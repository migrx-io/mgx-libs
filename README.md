# mgx-libs

Python library packages for migrx development


# Install 

    pip install git+https://github.com/migrx-io/mgx-libs.git

# Run tests

    export PYENV=/usr/bin PYTHONPATH=../mgx-libs/:$PYTHONPATH PYLINT_OPTS="R0902,W0703,W0707,C0103,C0114,C0115,C0116,R0201,C0209,R0904,R0801,W0201,C0415,C0411,C0412,E1121,R0912,R0903,R0915,R0914,R0911,R0401" LOGLEVEL=DEBUG MGX_DB_NAME=../mgx-libs/tests/data/test.db.local NODE_NAME=bb486ffe-25ac-46c0-8db8-d09029fbdc21 MGX_CASS_CREDS=dba:super MGX_DC_NAME=dc1 MGX_PLUGIN_SPEC="./actor.yaml" MGX_GW_TMP=../mgx-libs/tests/data/apispec.json
 
    make tests
