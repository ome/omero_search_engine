**Case Studies: Indexing Multiple Data Sources in a Single Deployment**

In one implemented deployment, the following data sources were indexed within the same IDR Searcher instance and made searchable together:

* IDR Data resource  ->  Database with sources metadata
* `SSBD <https://ssbd.riken.jp/database/>`_ Data resource -> use of CSV files exported from public resource and converted to the supported CSV format before indexing.
* `BIA <https://www.ebi.ac.uk/bioimage-archive/>`_ Data resource -> Data requiring conversion to CSV before indexing
* `OME 2024 NGFF Challenge <https://ome.github.io/ome2024-ngff-challenge/>`_  Data resource -> Data requiring conversion to CSV before indexing

All of these sources were indexed into the same search environment, enabling users to:

* Run queries across all resources simultaneously
* Filter results by one or multiple data resources
* Export combined search results seamlessly
* Use asynchronous search to fetch all results in one operation, or standard pagination for incremental retrieval.
* Export & Analyse:
  - Search results can be exported to CSV and Parquet formats.
   - The exported files are compatible with BFF for downstream filtering and data exploration.