Case Studies: Indexing Multiple Data Sources in a Single Deployment
===================================================================

Following data sources were indexed within the same IDR Searcher instance and made searchable together:

* IDR Data resource  ->  Database with source metadata
* `SSBD <https://ssbd.riken.jp/database/>`_ Data resource -> use of CSV files exported from public resource and converted to the supported CSV format before indexing.
* `BIA <https://www.ebi.ac.uk/bioimage-archive/>`_ Data resource -> Data requiring conversion to CSV before indexing
* `OME 2024 NGFF Challenge <https://ome.github.io/ome2024-ngff-challenge/>`_  Data resource -> Data requiring conversion to CSV before indexing

All of these sources were indexed into the same search environment, enabling:

* Simultaneous queries across all resources
* Filtering of results by one or multiple data resources
* Seamless export of combined search results
* Fetching of all results in one operation using asynchronous search
* Incremental retrieval of results using standard pagination
* Export & Analysis: Search results can be exported to CSV and Parquet formats. The exported files are compatible with BioFile Finder for downstream filtering and data exploration.
