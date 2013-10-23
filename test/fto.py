from pympi.Elan import Eaf

a = Eaf('fto.eaf')
a.createGapsAndOverlapsTier('a', 'b', 'fto-ab')
a.tofile('fto_out.eaf')
