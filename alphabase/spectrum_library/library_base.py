# AUTOGENERATED! DO NOT EDIT! File to edit: nbdev_nbs/spectrum_library/library_base.ipynb (unless otherwise specified).

__all__ = ['SpecLibBase']

# Cell
import pandas as pd
import numpy as np
import typing

import alphabase.peptide.fragment as fragment
import alphabase.peptide.precursor as precursor
from alphabase.io.hdf import HDF_File

class SpecLibBase(object):
    def __init__(self,
        # ['b_z1','b_z2','y_z1','y_modloss_z1', ...];
        # 'b_z1': 'b' is the fragment type and
        # 'z1' is the charge state z=1.
        charged_frag_types:typing.List[str] = [
            'b_z1','b_z2','y_z1', 'y_z2'
        ],
        min_precursor_mz = 400, max_precursor_mz = 6000,
        min_frag_mz = 200, max_frag_mz = 2000,
    ):
        self.charged_frag_types = charged_frag_types
        self._precursor_df = pd.DataFrame()
        self._fragment_intensity_df = pd.DataFrame()
        self._fragment_mz_df = pd.DataFrame()
        self.min_frag_mz = min_frag_mz
        self.max_frag_mz = max_frag_mz
        self.min_precursor_mz = min_precursor_mz
        self.max_precursor_mz = max_precursor_mz


    @property
    def precursor_df(self):
        return self._precursor_df

    @precursor_df.setter
    def precursor_df(self, df):
        self._precursor_df = df
        self.refine_df()

    def sort_by_nAA(self):
        if 'nAA' not in self._precursor_df.columns:
            self._precursor_df[
                'nAA'
            ] = self._precursor_df.sequence.str.len().astype(np.int32)
        self._precursor_df.sort_values('nAA', inplace=True)
        self._precursor_df.reset_index(drop=True, inplace=True)

    def refine_df(self):
        """
        To make sure all columns have desired dtype.
        This function also sorts `nAA`, and `reset_index` for fast prediction.
        """
        if self._precursor_df.charge.dtype not in ['int','int8','int64','int32']:
            self._precursor_df['charge'] = self._precursor_df['charge'].astype(int)

        if self._precursor_df.mod_sites.dtype not in ['O','U']:
            self._precursor_df['mod_sites'] = self._precursor_df.mod_sites.astype('U')

        self.sort_by_nAA()

    @property
    def fragment_mz_df(self):
        return self._fragment_mz_df

    @property
    def fragment_intensity_df(self):
        return self._fragment_intensity_df

    def clip_by_precursor_mz_(self):
        '''
        Clip self._precursor_df inplace
        '''
        self._precursor_df.drop(
            self._precursor_df.loc[
                (self._precursor_df['precursor_mz']<self.min_precursor_mz)|
                (self._precursor_df['precursor_mz']>self.max_precursor_mz)
            ].index, inplace=True
        )
        self._precursor_df.reset_index(drop=True, inplace=True)

    def mask_fragment_intensity_by_mz_(self):
        '''
        Clip self._fragment_intensity_df inplace.
        All clipped intensities are set as zeros.
        A more generic way is to use a mask.
        '''
        self._fragment_intensity_df[
            (self._fragment_mz_df<self.min_frag_mz)|
            (self._fragment_mz_df>self.max_frag_mz)
        ] = 0

    def load_fragment_df(self, **kwargs):
        precursor.reset_precursor_df(self._precursor_df)
        self.calc_fragment_mz_df(**kwargs)
        self.load_fragment_intensity_df(**kwargs)
        for col in self._fragment_mz_df.columns.values:
            if 'modloss' in col:
                self._fragment_intensity_df.loc[
                    self._fragment_mz_df[col]==0,col
                ] = 0

    def flatten_fragment_data(
        self
    )->typing.Tuple[np.array, np.array]:
        '''
        Create flattened (1-D) np.array for fragment mz and intensity
        dataframes, respectively. The arrays are references to
        original data, that means:
          1. This method is fast;
          2. Changing the array values will change the df values.
        They can be unraveled back using:
          `array.reshape(len(self._fragment_mz_df.columns), -1)`

        Returns:
            np.array: 1-D flattened mz array (a reference to
            original fragment mz df data)
            np.array: 1-D flattened intensity array (a reference to
            original fragment intensity df data)
        '''
        return (
            self._fragment_mz_df.values.reshape(-1),
            self._fragment_intensity_df.values.reshape(-1)
        )

    def load_fragment_intensity_df(self, **kwargs):
        '''
        All sub-class must re-implement this method.
        Fragment intensities can be predicted or from AlphaPept, or ...
        '''
        raise NotImplementedError(
            f'Sub-class of "{self.__class__}" must re-implement "load_fragment_intensity_df()"'
        )

    def calc_fragment_mz_df(self, **kwargs):
        if 'frag_start_idx' in self._precursor_df.columns:
            del self._precursor_df['frag_start_idx']
            del self._precursor_df['frag_end_idx']

        (
            self._fragment_mz_df
        ) = fragment.create_fragment_mz_dataframe(
            self._precursor_df, self.charged_frag_types
        )

    def calc_precursor_mz(self):
        fragment.update_precursor_mz(self._precursor_df)
        self.clip_by_precursor_mz_()

    def update_precursor_mz(self):
        self.calc_precursor_mz()

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
        return _hdf.library

    def _get_hdf_to_load(self,
        hdf_file,
    ):
        _hdf = HDF_File(
            hdf_file,
        )
        return _hdf.library

    def save_df_to_hdf(self,
        hdf_file:str,
        df_key: str,
        df: pd.DataFrame,
        delete_existing=False
    ):
        self._get_hdf_to_save(
            hdf_file,
            delete_existing=delete_existing
        ).add_group(df_key, df)

    def save_hdf(self, hdf_file):
        _hdf = HDF_File(
            hdf_file,
            read_only=False,
            truncate=True,
            delete_existing=True
        )
        _hdf.library = {
            'precursor_df': self._precursor_df,
            'fragment_mz_df': self._fragment_mz_df,
            'fragment_intensity_df': self._fragment_intensity_df,
        }

    def load_df_from_hdf(self,
        hdf_file:str,
        df_key: str
    ):
        return self._get_hdf_to_load(
            hdf_file
        ).__getattribute__(df_key).values

    def load_hdf(self, hdf_file):
        _hdf = HDF_File(
            hdf_file,
        )
        self._precursor_df = _hdf.library.precursor_df.values
        self._fragment_mz_df = _hdf.library.fragment_mz_df.values
        self._fragment_intensity_df = _hdf.library.fragment_intensity_df.values