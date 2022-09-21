# instructions
When a change is made to any OWL or TTL files, this is not reflected onto the generated HTML pages until the corresponding Python scripts are run.

The steps to accomplish this are as follows:
1. Apply changes to OWL or TTL files.
2. Run refresh.py, which runs nidm_html.py and nidm_schema.py (use Python3)
  * NOTE: This can take a long time to finish due to the amount of terms. Let it fully process, otherwise pages may appear blank.
3. Commit changes locally, then push changes to Github repository.
4. Verify the changes were applied to Github web pages.