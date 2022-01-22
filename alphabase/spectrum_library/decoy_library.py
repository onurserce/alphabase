# AUTOGENERATED! DO NOT EDIT! File to edit: nbdev_nbs/spectrum_library/decoy_library.ipynb (unless otherwise specified).

__all__ = ['DecoyLib', 'DiaNNDecoyLib', 'DecoyLibProvider', 'decoy_lib_provider']

# Cell
import copy
from alphabase.spectrum_library.library_base import SpecLibBase
from alphabase.io.hdf import HDF_File

class DecoyLib(SpecLibBase):
    def __init__(self,
        target_lib:SpecLibBase,
        fix_C_term = True,
        **kwargs,
    ):
        self.__dict__ = copy.deepcopy(target_lib.__dict__)
        self.target_lib = target_lib
        self.fix_C_term = fix_C_term

    def translate_to_decoy(self):
        self.decoy_sequence()
        self._decoy_mod()
        self._decoy_meta()
        self._decoy_frag()

    def decoy_sequence(self):
        self._decoy_seq()
        self._remove_target_seqs()

    def append_decoy_sequence(self):
        pass

    def _decoy_seq(self):
        (
            self._precursor_df.sequence
        ) = self._precursor_df.sequence.apply(
            lambda x: (x[:-1][::-1]+x[-1])
             if self.fix_C_term else x[::-1]
        )

    def _remove_target_seqs(self):
        target_seqs = set(
            self.target_lib._precursor_df.sequence.values
        )
        self._precursor_df.drop(
            self._precursor_df.loc[
                self._precursor_df.sequence.isin(target_seqs)
            ].index, inplace=True
        )

    def _decoy_meta(self):
        """
        Decoy for CCS/RT or other meta data
        """
        pass

    def _decoy_mod(self):
        """
        Decoy for modifications and modification sites
        """
        pass

    def _decoy_frag(self):
        """
        Decoy for fragment masses and intensities
        """
        self._decoy_fragment_mz()
        self._decoy_fragment_intensity()

    def _decoy_fragment_mz(self):
        pass

    def _decoy_fragment_intensity(self):
        pass

    def _get_hdf_to_save(self,
        hdf_file,
        delete_existing=False
    ):
        _hdf = HDF_File(
            hdf_file,
            read_only=False,
            truncate=True,
            delete_existing=delete_existing
        )
        return _hdf.library.decoy

    def _get_hdf_to_load(self,
        hdf_file,
    ):
        _hdf = HDF_File(
            hdf_file,
        )
        return _hdf.library.decoy

    def save_hdf(self, hdf_file):
        _hdf = HDF_File(
            hdf_file,
            read_only=False,
            truncate=True,
            delete_existing=False
        )
        _hdf.library.decoy = {
            'precursor_df': self._precursor_df,
            'fragment_mz_df': self._fragment_mz_df,
            'fragment_intensity_df': self._fragment_intensity_df,
        }

    def load_hdf(self, hdf_file):
        _hdf = HDF_File(
            hdf_file,
        )
        _hdf_lib = _hdf.library
        self._precursor_df = _hdf_lib.decoy.precursor_df.values
        self._fragment_mz_df = _hdf_lib.decoy.fragment_mz_df.values
        self._fragment_intensity_df = _hdf_lib.decoy.fragment_intensity_df.values

class DiaNNDecoyLib(DecoyLib):
    def __init__(self,
        target_lib:SpecLibBase,
        raw_AAs:str = 'GAVLIFMPWSCTYHKRQEND',
        mutated_AAs:str = 'LLLVVLLLLTSSSSLLNDQE', #DiaNN
        **kwargs,
    ):
        super().__init__(target_lib)
        self.raw_AAs = raw_AAs
        self.mutated_AAs = mutated_AAs

    def _decoy_seq(self):
        (
            self._precursor_df.sequence
        ) = self._precursor_df.sequence.apply(
            lambda x:
                x[0]+self.mutated_AAs[self.raw_AAs.index(x[1])]+
                x[2:-2]+self.mutated_AAs[self.raw_AAs.index(x[-2])]+x[-1]
        )

# Cell
class DecoyLibProvider(object):
    def __init__(self):
        self.decoy_dict = {}

    def register(self, name, decoy_class):
        self.decoy_dict[name.lower()] = decoy_class

    def get_decoy_lib(self, name,
        target_lib, **kwargs
    )->DecoyLib:
        return self.decoy_dict[name.lower()](
            target_lib, **kwargs
        )

decoy_lib_provider = DecoyLibProvider()
decoy_lib_provider.register('pseudo_reverse', DecoyLib)
decoy_lib_provider.register('diann', DiaNNDecoyLib)