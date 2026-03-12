Case Studies: Indexing multiple data sources in a single deployment
===================================================================

The following ata sources were indexed within the same IDR searcher instance and made searchable together:

* IDR data source: Database with source metadata.
* `SSBD <https://ssbd.riken.jp/database/>`_ Data source: use of CSV files exported from public resource and converted to the supported CSV format before indexing.
* `BIA <https://www.ebi.ac.uk/bioimage-archive/>`_ Data source: Data required conversion to CSV before indexing.
* `OME 2024 NGFF Challenge <https://ome.github.io/ome2024-ngff-challenge/>`_  Data source: Data required conversion to CSV before indexing

All of these sources were indexed into the same search environment, enabling:

* Simultaneous queries across all sources.
* Filtering of results by one or multiple data sources.
* Seamless export of combined search results.
* Fetching of all results in one operation using asynchronous searches.
* Incremental retrieval of results using standard pagination.
* Export and Analysis: Search results can be exported to CSV and Parquet formats. The exported files are compatible with BioFile Finder for downstream filtering and data exploration.
