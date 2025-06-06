import time
import logging
import traceback

from ged4py.parser import GedcomReader
from ged4py.model import Individual
from backend.utils.logger import get_file_logger

logger = get_file_logger("gedcom_core")


 

class GedcomCoreParser:
    def __init__(self, file_path):
        self.file_path = file_path

    def parse(self):
        """
        Parse the GEDCOM file using ged4py and return raw records.
        Logs:
        - Start and end time with duration
        - Counts of INDI, FAM, and other records
        - Any exceptions encountered
        """
        start_time = time.time()
        logger.info(f"📂 Starting GEDCOM parse: {self.file_path}")

        raw_individuals = []
        raw_families = []
        other_records = []
        total_records = 0

        try:
            with GedcomReader(self.file_path) as parser:
                for record in parser.records0():
                    total_records += 1
                    if isinstance(record, Individual):
                        raw_individuals.append(record)
                    elif record.tag == "FAM":
                        raw_families.append(record)
                    else:
                        other_records.append(record.tag)

        except Exception as e:
            logger.error("❌ Exception while parsing GEDCOM file:")
            logger.error(traceback.format_exc())
            raise

        end_time = time.time()
        elapsed = end_time - start_time

        logger.info(f"✅ GEDCOM parse complete: {self.file_path}")
        logger.info(f"🕒 Elapsed time: {elapsed:.2f} seconds")
        logger.info(f"📊 Parsed records - INDI: {len(raw_individuals)}, FAM: {len(raw_families)}, OTHER: {len(other_records)}, TOTAL: {total_records}")

        return {
            "individuals": raw_individuals,
            "families": raw_families,
            "others": other_records
        }
