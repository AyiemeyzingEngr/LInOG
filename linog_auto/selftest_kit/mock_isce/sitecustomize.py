# MOCK env only (linog_auto self-test): new shelves in dbm.dumb (data.dat, .dir, .bak), the format felix writes
# (RD2) and the kit's checks glob for; a Python with ndbm would otherwise write data.db
import dbm
dbm._names = ['dbm.dumb']
