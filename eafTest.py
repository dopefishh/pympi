from Elan import Eaf
import timeit
import pdb

eafObj = Eaf('./t.eaf')
eafObj.createGapsAndOverlapsTier('Tolk S1', 'Tolk S2', 'Test')
eafObj.tofile('./tt.eaf')

print timeit.timeit("lst = list()")
print timeit.timeit("lst = []")

