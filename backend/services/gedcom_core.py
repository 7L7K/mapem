#os.path.expanduser("~")/mapem/backend/services/gedcom_core.py

from ged4py.parser import GedcomReader
from ged4py.model import Individual

class GedcomCoreParser:
    def __init__(self, file_path):
        self.file_path = file_path

    def parse(self):
        """
        Parse the GEDCOM file using ged4py and return raw records.
        Returns a dictionary with lists of raw individual and family records.
        """
        raw_individuals = []
        raw_families = []

        with GedcomReader(self.file_path) as parser:
            for record in parser.records0():
                if isinstance(record, Individual):
                    raw_individuals.append(record)
                elif record.tag == "FAM":
                    raw_families.append(record)
        return {
            "individuals": raw_individuals,
            "families": raw_families
        }
