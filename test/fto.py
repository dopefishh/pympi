from pympi.Elan import Eaf

a = Eaf()
a.addTier('speaker_a')
a.addTier('speaker_b')

a.insertAnnotation('speaker_a', 1, 500, 'a')
a.insertAnnotation('speaker_a', 1000, 2000, 'a')
a.insertAnnotation('speaker_a', 3000, 4500, 'a')
a.insertAnnotation('speaker_b', 1500, 2500, 'b')
a.insertAnnotation('speaker_b', 3500, 4000, 'b')

a.createGapsAndOverlapsTier('speaker_a', 'speaker_b')

a.tofile('fto.eaf')
a.tofileXMLbeta('ftox.eaf')
