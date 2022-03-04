from pyalign.problems.instance import MatrixProblem, IndexedMatrixProblem
from pyalign.problems.function import *
from pyalign.problems.function import Function

from typing import Sequence


class Problem(MatrixProblem):
	"""
	A Problem induced by some binary function \(f(x, y)\).
	"""

	def __init__(self, f, s, t, **kwargs):
		super().__init__((len(s), len(t)), s, t, **kwargs)
		self._f = f

	def build_matrix(self, out):
		for i, x in enumerate(self.s):
			for j, y in enumerate(self.t):
				out[i, j] = self._f(x, y)


class ProblemFactory:
	"""
	A factory for problems that can be built from some binary function
	\(f(x, y)\).
	"""

	def __init__(self, w: callable, direction="maximize", dtype=np.float32):
		"""

		Parameters
		----------
		w : callable
			\(w(x, y)\) that gives a measure of affinity (or distance) between
			two arbitrary elements (e.g. characters) \(x\) and \(y\).
		direction : {'minimize', 'maximize'}
			direction of problems created by this factory, i.e. whether
			\(w\) gives affinity or distance
		dtype : type
			dtype of values returned by \(f\)
		"""

		if w is None and direction == "minimize":
			from scipy.spatial.distance import euclidean
			w = euclidean

		self._w = w
		self._direction = direction
		self._dtype = dtype

	def new_problem(self, s, t):
		"""
		Creates a new alignment problem for the sequences \(s\) and \(t\)

		Parameters
		----------
		s : array_like
			first sequence
		t : array_like
			second sequence

		Returns
		-------
		Problem modelling optimal alignment between \(s\) and \(t\)
		"""

		return Problem(
			self._w, s, t,
			direction=self._direction,
			dtype=self._dtype)


general = ProblemFactory


class AlphabetProblem(IndexedMatrixProblem):
	def __init__(self, matrix, encoder, *args, **kwargs):
		self._matrix = matrix
		self._encoder = encoder
		super().__init__(*args, **kwargs)

	def similarity_lookup_table(self):
		return self._matrix

	def build_index_sequences(self, a, b):
		encoder = self._encoder
		encoder.encode(self._s, out=a)
		encoder.encode(self._t, out=b)


class Encoder:
	def __init__(self, alphabet):
		self._alphabet = tuple(set(alphabet))
		self._ids = dict((k, i) for i, k in enumerate(self._alphabet))

	def encode(self, s, out=None):
		ids = self._ids
		if out is None:
			return [ids[x] for x in s]
		else:
			for i, x in enumerate(s):
				out[i] = ids[x]

	@property
	def alphabet(self):
		return self._alphabet


class AlphabetProblemFactory:
	"""
	A factory for alignment problems involving sequences \(s, t\) that can be
	written using a small fixed alphabet \(\Omega\) such that \(∀i: s_i \in
	\Omega\), \(∀j: t_j \in \Omega\).
	"""

	def __init__(self, alphabet: Sequence, w: callable, direction="maximize", dtype=np.float32):
		"""
		Parameters
		----------
		alphabet : Sequence
			fixed alphabet \Omega
		w : callable
			\(w(x, y)\) that gives a measure of affinity (or distance) between
			two arbitrary elements (e.g. characters) \(x\) and \(y\).
		direction : {'minimize', 'maximize'}
			direction of problems created by this factory, i.e. whether
			\(w\) gives affinity or distance
		dtype
			dtype of values returned by \(f\)
		"""

		self._encoder = Encoder(alphabet)
		ordered_alphabet = self._encoder.alphabet
		n = len(ordered_alphabet)
		self._matrix = np.empty((n, n), dtype=np.float32)
		if isinstance(w, Function):
			w.build_matrix(self._encoder, self._matrix)
		else:
			for i, x in enumerate(ordered_alphabet):
				for j, y in enumerate(ordered_alphabet):
					self._matrix[i, j] = w(i, j)
		self._direction = direction
		self._dtype = dtype

	def new_problem(self, s, t):
		return AlphabetProblem(
			self._matrix, self._encoder, (len(s), len(t)), s, t,
			direction=self._direction, dtype=self._dtype)


alphabetic = AlphabetProblemFactory
