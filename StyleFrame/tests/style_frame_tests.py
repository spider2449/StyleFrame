import unittest
import pandas as pd
import os

from functools import partial
from StyleFrame import Container, StyleFrame, Styler, utils
from StyleFrame.tests import TEST_FILENAME


class StyleFrameTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.styler_obj_1 = Styler(bg_color=utils.colors.blue, bold=True, font='Impact', font_color=utils.colors.yellow,
                                  font_size=20, underline=utils.underline.single,
                                  horizontal_alignment=utils.horizontal_alignments.left,
                                  vertical_alignment=utils.vertical_alignments.center,
                                  comment_text='styler_obj_1 comment')
        cls.styler_obj_2 = Styler(bg_color=utils.colors.yellow, comment_text='styler_obj_2 comment')
        cls.openpy_style_obj_1 = cls.styler_obj_1.to_openpyxl_style()
        cls.openpy_style_obj_2 = cls.styler_obj_2.to_openpyxl_style()

    def setUp(self):
        self.ew = StyleFrame.ExcelWriter(TEST_FILENAME)
        self.sf = StyleFrame({'a': ['col_a_row_1', 'col_a_row_2', 'col_a_row_3'],
                              'b': ['col_b_row_1', 'col_b_row_2', 'col_b_row_3']})
        self.apply_column_style = partial(self.sf.apply_column_style, styler_obj=self.styler_obj_1, width=10)
        self.apply_style_by_indexes = partial(self.sf.apply_style_by_indexes, styler_obj=self.styler_obj_1, height=10)
        self.apply_headers_style = partial(self.sf.apply_headers_style, styler_obj=self.styler_obj_1)

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(TEST_FILENAME)
        except OSError as ex:
            print(ex)

    def export_and_get_default_sheet(self, save=False):
        self.sf.to_excel(excel_writer=self.ew, right_to_left=True, columns_to_hide=self.sf.columns[0],
                         row_to_add_filters=0, columns_and_rows_to_freeze='A2', allow_protection=True)
        if save:
            self.ew.save()
        return self.ew.book.get_sheet_by_name('Sheet1')

    def test_init_styler_obj(self):
        self.sf = StyleFrame({'a': [1, 2, 3], 'b': [1, 2, 3]}, styler_obj=self.styler_obj_1)

        self.assertTrue(all(self.sf.at[index, 'a'].style.to_openpyxl_style() == self.openpy_style_obj_1
                            for index in self.sf.index))

        sheet = self.export_and_get_default_sheet()

        self.assertTrue(all(sheet.cell(row=i, column=j).style == self.openpy_style_obj_1
                            for i in range(2, len(self.sf))
                            for j in range(1, len(self.sf.columns))))

        with self.assertRaises(TypeError):
            StyleFrame({}, styler_obj=1)

    def test_init_dataframe(self):
        self.assertIsInstance(StyleFrame(pd.DataFrame({'a': [1, 2, 3], 'b': [1, 2, 3]})), StyleFrame)
        self.assertIsInstance(StyleFrame(pd.DataFrame()), StyleFrame)

    def test_init_styleframe(self):
        self.assertIsInstance(StyleFrame(StyleFrame({'a': [1, 2, 3]})), StyleFrame)

        with self.assertRaises(TypeError):
            StyleFrame({}, styler_obj=1)

    def test_len(self):
        self.assertEqual(len(self.sf), len(self.sf.data_df))
        self.assertEqual(len(self.sf), 3)

    def test_str(self):
        self.assertEqual(str(self.sf), str(self.sf.data_df))

    def test__getitem__(self):
        self.assertEqual(self.sf['a'].tolist(), self.sf.data_df['a'].tolist())
        self.assertTrue(self.sf.data_df[['a', 'b']].equals(self.sf[['a', 'b']].data_df))

    def test__setitem__(self):
        self.sf['a'] = range(3)
        self.sf['b'] = range(3, 6)
        self.sf['c'] = 5
        self.sf['d'] = self.sf['a'] + self.sf['b']
        self.sf['e'] = self.sf['a'] + 5

        self.assertTrue(all(self.sf.applymap(lambda x: isinstance(x, Container)).all()))

    def test__getattr__(self):
        self.assertEqual(self.sf.fillna, self.sf.data_df.fillna)
        self.assertTrue(self.sf['a'].equals(self.sf.a))

        with self.assertRaises(AttributeError):
            self.sf.non_exisiting_method()

    def test_apply_column_style(self):
        # testing some edge cases
        with self.assertRaises(TypeError):
            # noinspection PyTypeChecker
            self.sf.apply_column_style(cols_to_style='a', styler_obj=0)

        with self.assertRaises(KeyError):
            self.sf.apply_column_style(cols_to_style='non_existing_col', styler_obj=Styler())

        # actual tests
        self.apply_column_style(cols_to_style=['a'])
        self.assertTrue(all([self.sf.at[index, 'a'].style.to_openpyxl_style() == self.openpy_style_obj_1
                             and self.sf.at[index, 'b'].style.to_openpyxl_style() != self.openpy_style_obj_1
                             for index in self.sf.index]))

        sheet = self.export_and_get_default_sheet()

        self.assertEqual(sheet.column_dimensions['A'].width, 10)

        # range starts from 2 since we don't want to check the header's style
        self.assertTrue(all(sheet.cell(row=i, column=1).style == self.openpy_style_obj_1 for i in range(2, len(self.sf))))

    def test_apply_style_by_indexes_single_col(self):
        with self.assertRaises(TypeError):
            # noinspection PyTypeChecker
            self.sf.apply_style_by_indexes(indexes_to_style=0, styler_obj=0)

        self.apply_style_by_indexes(self.sf[self.sf['a'] == 'col_a_row_2'], cols_to_style=['a'])

        self.assertTrue(all(self.sf.at[index, 'a'].style.to_openpyxl_style() == self.openpy_style_obj_1
                            for index in self.sf.index if self.sf.at[index, 'a'] == 'col_a_row_2'))

        sheet = self.export_and_get_default_sheet()

        self.assertTrue(all(sheet.cell(row=i, column=1).style == self.openpy_style_obj_1 for i in range(1, len(self.sf))
                            if sheet.cell(row=i, column=1).value == 2))

        self.assertEqual(sheet.row_dimensions[3].height, 10)

    def test_apply_style_by_indexes_all_cols(self):
        self.apply_style_by_indexes(self.sf[self.sf['a'] == 2])

        self.assertTrue(all(self.sf.at[index, 'a'].style.to_openpyxl_style() == self.openpy_style_obj_1
                            for index in self.sf.index if self.sf.at[index, 'a'] == 2))

        sheet = self.export_and_get_default_sheet()

        self.assertTrue(all(sheet.cell(row=i, column=j).style == self.openpy_style_obj_1
                            for i in range(1, len(self.sf))
                            for j in range(1, len(self.sf.columns))
                            if sheet.cell(row=i, column=1).value == 2))

    def test_apply_style_by_indexes_complement_style(self):
        self.apply_style_by_indexes(self.sf[self.sf['a'] == 'col_a_row_1'], complement_style=self.styler_obj_2)

        self.assertTrue(all(self.sf.at[index, 'a'].style.to_openpyxl_style() == self.openpy_style_obj_1
                            for index in self.sf.index if self.sf.at[index, 'a'] == 'col_a_row_1'))

        self.assertTrue(all(self.sf.at[index, 'a'].style.to_openpyxl_style() == self.openpy_style_obj_2
                            for index in self.sf.index if self.sf.at[index, 'a'] != 'col_a_row_1'))

    def test_apply_style_by_indexes_with_single_index(self):
        self.apply_style_by_indexes(self.sf.index[0])

        self.assertTrue(all(self.sf.iloc[0, self.sf.columns.get_loc(col)].style.to_openpyxl_style() == self.openpy_style_obj_1
                            for col in self.sf.columns))

        sheet = self.export_and_get_default_sheet()

        # row=2 since sheet start from row 1 and the headers are row 1
        self.assertTrue(all(sheet.cell(row=2, column=col).style == self.openpy_style_obj_1
                            for col in range(1, len(self.sf.columns))))

    def test_apply_style_by_indexes_all_cols_with_multiple_indexes(self):
        self.apply_style_by_indexes([1, 2])

        self.assertTrue(all(self.sf.iloc[index, self.sf.columns.get_loc(col)].style.to_openpyxl_style() == self.openpy_style_obj_1
                            for index in [1, 2]
                            for col in self.sf.columns))

        sheet = self.export_and_get_default_sheet()

        self.assertTrue(all(sheet.cell(row=i, column=j).style == self.openpy_style_obj_1
                            for i in [3, 4]  # sheet start from row 1 and headers are row 1
                            for j in range(1, len(self.sf.columns))))

    def test_apply_headers_style(self):
        self.apply_headers_style()
        self.assertEqual(self.sf.columns[0].style.to_openpyxl_style(), self.openpy_style_obj_1)

        sheet = self.export_and_get_default_sheet()
        self.assertEqual(sheet.cell(row=1, column=1).style, self.openpy_style_obj_1)

    def test_set_column_width(self):
        # testing some edge cases
        with self.assertRaises(TypeError):
            # noinspection PyTypeChecker
            self.sf.set_column_width(columns='a', width='a')
        with self.assertRaises(ValueError):
            # noinspection PyTypeChecker
            self.sf.set_column_width(columns='a', width=-1)

        # actual tests
        self.sf.set_column_width(columns=['a'], width=20)
        self.assertEqual(self.sf._columns_width['a'], 20)

        sheet = self.export_and_get_default_sheet()

        self.assertEqual(sheet.column_dimensions['A'].width, 20)

    def test_set_column_width_dict(self):
        with self.assertRaises(TypeError):
            # noinspection PyTypeChecker
            self.sf.set_column_width_dict(None)

        width_dict = {'a': 20, 'b': 30}
        self.sf.set_column_width_dict(width_dict)
        self.assertEqual(self.sf._columns_width, width_dict)

        sheet = self.export_and_get_default_sheet()

        self.assertTrue(all(sheet.column_dimensions[col.upper()].width == width_dict[col]
                            for col in width_dict))

    def test_set_row_height(self):
        # testing some edge cases
        with self.assertRaises(TypeError):
            self.sf.set_row_height(rows=[1], height='a')
        with self.assertRaises(ValueError):
            self.sf.set_row_height(rows=[1], height=-1)
        with self.assertRaises(ValueError):
            self.sf.set_row_height(rows=['a'], height=-1)

        # actual tests
        self.sf.set_row_height(rows=[1], height=20)
        self.assertEqual(self.sf._rows_height[1], 20)

        sheet = self.export_and_get_default_sheet()

        self.assertEqual(sheet.row_dimensions[1].height, 20)

    def test_set_row_height_dict(self):
        with self.assertRaises(TypeError):
            # noinspection PyTypeChecker
            self.sf.set_row_height_dict(None)

        height_dict = {1: 20, 2: 30}
        self.sf.set_row_height_dict(height_dict)
        self.assertEqual(self.sf._rows_height, height_dict)

        sheet = self.export_and_get_default_sheet()

        self.assertTrue(all(sheet.row_dimensions[row].height == height_dict[row]
                            for row in height_dict))

    def test_rename(self):
        with self.assertRaises(TypeError):
            # noinspection PyTypeChecker
            self.sf.rename(columns=None)

        original_columns_name = list(self.sf.columns)

        names_dict = {'a': 'A', 'b': 'B'}
        # testing rename with inplace = True
        self.sf.rename(columns=names_dict, inplace=True)

        self.assertTrue(all(new_col_name in self.sf.columns
                            for new_col_name in names_dict.values()))

        new_columns_name = list(self.sf.columns)
        # check that the columns order did not change after renaming
        self.assertTrue(all(original_columns_name.index(old_col_name) == new_columns_name.index(new_col_name)
                            for old_col_name, new_col_name in names_dict.items()))

        # using the old name should raise a KeyError
        with self.assertRaises(KeyError):
            # noinspection PyStatementEffect
            self.sf['a']

        # testing rename with inplace = False
        names_dict = {v: k for k, v in names_dict.items()}
        new_sf = self.sf.rename(columns=names_dict, inplace=False)
        self.assertTrue(all(new_col_name in new_sf.columns
                            for new_col_name in names_dict.values()))

        # using the old name should raise a KeyError
        with self.assertRaises(KeyError):
            # noinspection PyStatementEffect
            new_sf['A']

    def test_read_excel_no_style(self):
        self.export_and_get_default_sheet(save=True)
        sf_from_excel = StyleFrame.read_excel(TEST_FILENAME)
        # making sure content is the same
        self.assertTrue(all(list(self.sf[col]) == list(sf_from_excel[col]) for col in self.sf.columns))

    def test_read_excel_with_style_openpyxl_objects(self):
        self.export_and_get_default_sheet(save=True)
        sf_from_excel = StyleFrame.read_excel(TEST_FILENAME, read_style=True)
        # making sure content is the same
        self.assertTrue(all(list(self.sf[col]) == list(sf_from_excel[col]) for col in self.sf.columns))

        rows_in_excel = sf_from_excel.data_df.itertuples()
        rows_in_self = self.sf.data_df.itertuples()

        # making sure styles are the same
        self.assertTrue(all(excel_cell.style == self_cell.style
                            # the dataframe's index's styles should be Styler object because
                            # we don't save the indexes to the excel in the tests
                            if index == 0
                            else self_cell.style == Styler.from_openpyxl_style(excel_cell.style, [])
                            for row_in_excel, row_in_self in zip(rows_in_excel, rows_in_self)
                            for index, (excel_cell, self_cell) in enumerate(zip(row_in_excel, row_in_self))))

    def test_read_excel_with_style_styler_objects(self):
        self.export_and_get_default_sheet(save=True)
        sf_from_excel = StyleFrame.read_excel(TEST_FILENAME, read_style=True, use_openpyxl_styles=False)
        # making sure content is the same
        self.assertTrue(all(list(self.sf[col]) == list(sf_from_excel[col]) for col in self.sf.columns))

        rows_in_excel = sf_from_excel.data_df.itertuples()
        rows_in_self = self.sf.data_df.itertuples()

        # making sure styles are the same
        self.assertTrue(all(excel_cell.style == self_cell.style
                        for row_in_excel, row_in_self in zip(rows_in_excel, rows_in_self)
                        for excel_cell, self_cell in zip(row_in_excel, row_in_self)))

    def test_read_excel_with_style_comments_openpyxl_objects(self):
        self.export_and_get_default_sheet(save=True)
        sf_from_excel = StyleFrame.read_excel(TEST_FILENAME, read_style=True, read_comments=True)
        # making sure content is the same
        self.assertTrue(all(list(self.sf[col]) == list(sf_from_excel[col]) for col in self.sf.columns))

        rows_in_excel = sf_from_excel.data_df.itertuples()
        rows_in_self = self.sf.data_df.itertuples()

        # making sure styles are the same
        self.assertTrue(all(excel_cell.style == self_cell.style
                            # the dataframe's index's styles should be Styler object because
                            # we don't save the indexes to the excel in the tests
                            if index == 0
                            else self_cell.style == Styler.from_openpyxl_style(excel_cell.style, [])
                            for row_in_excel, row_in_self in zip(rows_in_excel, rows_in_self)
                            for index, (excel_cell, self_cell) in enumerate(zip(row_in_excel, row_in_self))))

    def test_read_excel_with_style_comments_styler_objects(self):
        self.export_and_get_default_sheet(save=True)
        sf_from_excel = StyleFrame.read_excel(TEST_FILENAME, read_style=True, use_openpyxl_styles=False,
                                              read_comments=True)
        # making sure content is the same
        self.assertTrue(all(list(self.sf[col]) == list(sf_from_excel[col]) for col in self.sf.columns))

        rows_in_excel = sf_from_excel.data_df.itertuples()
        rows_in_self = self.sf.data_df.itertuples()

        # making sure styles are the same
        self.assertTrue(all(excel_cell.style == self_cell.style
                            for row_in_excel, row_in_self in zip(rows_in_excel, rows_in_self)
                            for excel_cell, self_cell in zip(row_in_excel, row_in_self)))

    def test_read_excel_style_and_save(self):
        StyleFrame.read_excel(TEST_FILENAME, read_style=True).to_excel(TEST_FILENAME).save()

    def test_row_indexes(self):
        self.assertEqual(self.sf.row_indexes, (1, 2, 3, 4))

    def test_style_alternate_rows(self):
        styles = [self.styler_obj_1, self.styler_obj_2]
        openpy_styles = [self.openpy_style_obj_1, self.openpy_style_obj_2]
        self.sf.style_alternate_rows(styles)

        self.assertTrue(all(self.sf.iloc[index.value, 0].style.to_openpyxl_style() == styles[index.value % len(styles)].to_openpyxl_style()
                            for index in self.sf.index))

        sheet = self.export_and_get_default_sheet()

        # sheet start from row 1 and headers are row 1, so need to add 2 when iterating
        self.assertTrue(all(sheet.cell(row=i.value + 2, column=1).style == openpy_styles[i.value % len(styles)]
                            for i in self.sf.index))

    def test_add_color_scale_conditional_formatting_start_end(self):
        self.sf.add_color_scale_conditional_formatting(start_type=utils.conditional_formatting_types.percentile,
                                                       start_value=0, start_color=utils.colors.red,
                                                       end_type=utils.conditional_formatting_types.percentile,
                                                       end_value=100, end_color=utils.colors.green)
        sheet = self.export_and_get_default_sheet(save=True)
        rules_dict = sheet.conditional_formatting.cf_rules['A1:B4']
        self.assertEqual(rules_dict[0]['type'], 'colorScale')
        self.assertEqual(rules_dict[0]['colorScale']['color'][0].rgb, utils.colors.red)
        self.assertEqual(rules_dict[0]['colorScale']['color'][1].rgb, utils.colors.green)
        self.assertEqual(rules_dict[0]['colorScale']['cfvo'][0]['type'], utils.conditional_formatting_types.percentile)
        self.assertEqual(rules_dict[0]['colorScale']['cfvo'][0]['val'], '0')
        self.assertEqual(rules_dict[0]['colorScale']['cfvo'][1]['type'], utils.conditional_formatting_types.percentile)
        self.assertEqual(rules_dict[0]['colorScale']['cfvo'][1]['val'], '100')

    def test_add_color_scale_conditional_formatting_start_mid_end(self):
        self.sf.add_color_scale_conditional_formatting(start_type=utils.conditional_formatting_types.percentile,
                                                       start_value=0, start_color=utils.colors.red,
                                                       mid_type=utils.conditional_formatting_types.percentile,
                                                       mid_value=50, mid_color=utils.colors.yellow,
                                                       end_type=utils.conditional_formatting_types.percentile,
                                                       end_value=100, end_color=utils.colors.green)
        sheet = self.export_and_get_default_sheet(save=True)
        rules_dict = sheet.conditional_formatting.cf_rules['A1:B4']

        self.assertEqual(rules_dict[0]['type'], 'colorScale')
        self.assertEqual(rules_dict[0]['colorScale']['color'][0].rgb, utils.colors.red)
        self.assertEqual(rules_dict[0]['colorScale']['color'][1].rgb, utils.colors.yellow)
        self.assertEqual(rules_dict[0]['colorScale']['color'][2].rgb, utils.colors.green)
        self.assertEqual(rules_dict[0]['colorScale']['cfvo'][0]['type'], utils.conditional_formatting_types.percentile)
        self.assertEqual(rules_dict[0]['colorScale']['cfvo'][0]['val'], '0')
        self.assertEqual(rules_dict[0]['colorScale']['cfvo'][1]['type'], utils.conditional_formatting_types.percentile)
        self.assertEqual(rules_dict[0]['colorScale']['cfvo'][1]['val'], '50')
        self.assertEqual(rules_dict[0]['colorScale']['cfvo'][2]['type'], utils.conditional_formatting_types.percentile)
        self.assertEqual(rules_dict[0]['colorScale']['cfvo'][2]['val'], '100')
