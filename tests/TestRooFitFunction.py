
import unittest

from roofit_functional.RooFitFunction import RooFitFunction, RooFitVar

class TestRooFitFunction(unittest.TestCase):

    def setUp(self):
        self.x_limits = {'x': [-1, 1]}
        self.param_dict = {'mu': [0, -1, 1], 'sigma': [1, 0.5, 1.5]}
        self.function_type = 'Gaussian'
        self.name = 'Gauss'
        self.pdf = RooFitFunction(self.name, self.x_limits, self.function_type, self.param_dict)

    def test_initialization(self):
        self.assertEqual(self.pdf.name, self.name)
        self.assertEqual(self.pdf.x_limits, self.x_limits)
        self.assertEqual(self.pdf.function_type, self.function_type)
        self.assertEqual(self.pdf.param_dict, self.param_dict)
        self.assertIsNotNone(self.pdf.function)

    def test_invalid_x_limits_type(self):
        with self.assertRaises(TypeError):
            RooFitFunction(self.name, ['not', 'a', 'dict'], self.function_type, self.param_dict)

    def test_invalid_param_dict_type(self):
        with self.assertRaises(TypeError):
            RooFitFunction(self.name, self.x_limits, self.function_type, ['not', 'a', 'dict'])

    def test_invalid_function_type(self):
        with self.assertRaises(AttributeError):
            RooFitFunction(self.name, self.x_limits, 'NotImplementedType', self.param_dict)

    def test_invalid_param_dict_length(self):
        with self.assertRaises(TypeError):
            RooFitFunction(self.name, self.x_limits, 'Uniform', {'mu': [0, -1, 1]})

    def test_get_add_valid(self):
        other = RooFitFunction('Gauss2', {'all': self.pdf}, self.function_type, self.param_dict)
        frac = {'frac': [0.5, 0.0, 1.0]}
        result = self.pdf.get_add(other, frac)
        self.assertIsInstance(result, RooFitFunction)
        self.assertIn('frac', result.param_dict)

    def test_get_add_invalid_type(self):
        with self.assertRaises(TypeError):
            self.pdf.get_add('not_a_pdf', {'frac': [0.5, 0.0, 1.0]})

    def test_get_add_invalid_frac_type(self):
        other = RooFitFunction('Gauss2', self.x_limits, self.function_type, self.param_dict)
        with self.assertRaises(TypeError):
            self.pdf.get_add(other, ['not', 'a', 'dict'])

    def test_get_add_invalid_frac_length(self):
        other = RooFitFunction('Gauss2', self.x_limits, self.function_type, self.param_dict)
        with self.assertRaises(ValueError):
            self.pdf.get_add(other, {'frac1': [0.5, 0.0, 1.0], 'frac2': [0.5, 0.0, 1.0]})

    def test_get_convolution_valid(self):
        other = RooFitFunction('Gauss2', {'all': self.pdf}, self.function_type, self.param_dict)
        result = self.pdf.get_convolution(other)
        self.assertIsInstance(result, RooFitFunction)

    def test_get_convolution_invalid_type(self):
        with self.assertRaises(TypeError):
            self.pdf.get_convolution('not_a_pdf')

    def test_set_fixed_valid(self):
        self.pdf.set_fixed({'mu': 0.1})
        self.assertEqual(self.pdf.param_dict['mu'], 0.1)

    def test_set_fixed_invalid_type(self):
        with self.assertRaises(TypeError):
            self.pdf.set_fixed(['not', 'a', 'dict'])

    def test_set_fixed_invalid_value_type(self):
        with self.assertRaises(TypeError):
            self.pdf.set_fixed({'mu': 'not_a_number'})

    def test_set_floated_valid(self):
        self.pdf.set_floated({'mu': [0.2, -1, 1]})
        self.assertEqual(self.pdf.param_dict['mu'], [0.2, -1, 1])

    def test_set_floated_invalid_type(self):
        with self.assertRaises(TypeError):
            self.pdf.set_floated(['not', 'a', 'dict'])

    def test_set_floated_invalid_value_type(self):
        with self.assertRaises(TypeError):
            self.pdf.set_floated({'mu': 'not_a_list'})

    def test_set_limits_valid_list(self):
        self.pdf.set_limits([-2, 2])
        self.assertEqual(self.pdf.x_limits['x'], [-2, 2])

    def test_set_limits_valid_dict(self):
        self.pdf.set_limits({'x': [-3, 3]})
        self.assertEqual(self.pdf.x_limits['x'], [-3, 3])

    def test_set_limits_invalid_type(self):
        with self.assertRaises(TypeError):
            self.pdf.set_limits('not_a_dict_or_list')

    def test_set_limits_invalid_value_type(self):
        with self.assertRaises(TypeError):
            self.pdf.set_limits({'x': 'not_a_list'})

    def test_get_NFitFloated(self):
        self.pdf.set_fixed({'mu': 0.1})
        self.assertEqual(self.pdf.get_NFitFloated(), 1)

    def test_mul_with_RooFitVar(self):
        var = RooFitVar({'x': [-1, 1]}, 'mu*x', {'mu': [1, 0, 2]}, 'var')
        result = self.pdf * var
        self.assertIsInstance(result, RooFitVar)

#    @unittest.expectedFailure
    def test_mul_with_RooFitFunction(self):
        other = RooFitFunction('Gauss1', {'z': [-3, 3]}, self.function_type, self.param_dict)
        result = self.pdf * other
        self.assertIsInstance(result, RooFitFunction)

    def test_mul_invalid_type(self):
        with self.assertRaises(ArithmeticError):
            self.pdf * 'not_a_pdf'

if __name__ == '__main__':
    unittest.main()
