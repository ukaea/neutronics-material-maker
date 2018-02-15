
import re
import sys
import json
import pprint

from isotope import Isotope
from common_utils import find_symbol_from_protons
from common_utils import find_protons_from_symbol
from common_utils import natural_isotopes_in_elements

from jsonable_object import NamedObject

class Element(NamedObject):
    def __init__(self, symbol_or_proton, enriched_isotopes='Natural'):
        super(Element, self).__init__()

        if type(symbol_or_proton) == int or symbol_or_proton.isdigit():
            self.protons = symbol_or_proton
            self.symbol = find_symbol_from_protons(symbol_or_proton)
        else:
            self.symbol = symbol_or_proton
            self.protons = find_protons_from_symbol(symbol_or_proton)


        if enriched_isotopes == 'Natural':
            self.enriched_isotopes = 'Natural'
        else:
            self.enriched_isotopes = enriched_isotopes


    @property
    def molar_mass_g(self):
        element_mass = 0
        for isotope in self.isotopes:
            # isotope.print_details
            print('element_mass',element_mass,'isotope.abundance',isotope.abundance, 'isotope.mass_amu',isotope.mass_amu)
            element_mass = element_mass + isotope.abundance * isotope.mass_amu
        return element_mass

    @property
    def isotopes(self):
        isotopes_to_make = []
        # print('enriched isotopes = ',self.enriched_isotopes)
        if self.enriched_isotopes!='Natural':
            # print('enriched isotope detected',self.symbol)
            # check that ratios add up to 1
            cummulative_abundance = 0.0
            for enriched_isotope in self.enriched_isotopes:
                cummulative_abundance = cummulative_abundance + enriched_isotope.abundance
                if enriched_isotope.abundance < 0 or enriched_isotope.abundance > 1.0:
                    print('Enriched isotopes fractions must be between 0 and 1.0, you have', enriched_isotope.abundance)
                    sys.exit()
            if cummulative_abundance != 1.0:
                print('Enriched isotopes fractions must add up to 1.0, you have', cummulative_abundance)
                sys.exit()

            # check if all isotopes for element are present
            required_isotope_list = natural_isotopes_in_elements(self.symbol)
            if len(self.enriched_isotopes) != len(required_isotope_list):
                print(
                'Your number of enriched isotopes does not match the number of isotopes in the natural element composition')
                print('you have ', len(self.enriched_isotopes), ' but element ', self.symbol, ' needs ',
                      len(required_isotope_list))
                sys.exit()

            # checks each of the natural isotopes is represented in the list
            for enriched_isotope, required_isotope in zip(self.enriched_isotopes, required_isotope_list):
                if enriched_isotope.symbol != required_isotope.symbol:
                    print('Enriched isotope symbol is wrong', enriched_isotope.symbol, required_isotope.symbol)
                    sys.exit()
                if enriched_isotope.atomic_number != required_isotope.atomic_number:
                    print('Enriched isotope atomic numbers are not the same as natural material, provided',
                          enriched_isotope.atomic_number, ' is not equal to required ', required_isotope.atomic_number)
                    sys.exit()

            for enriched_isotope in self.enriched_isotopes:
                isotopes_to_make.append(enriched_isotope)

        else:
            # print('no enriched isotopes found')
            isotopes_to_make = natural_isotopes_in_elements(self.symbol)

        return isotopes_to_make

