-- Fix known financial-holding subsidiary job mappings.
-- Safe to rerun: updates only matched job rows.

UPDATE jobs
SET stock_id = '8299'
WHERE company_name LIKE '%群聯%'
   OR company_name LIKE '%Phison%';

UPDATE jobs
SET stock_id = '2880'
WHERE company_name LIKE '%華南金融控股%'
   OR company_name LIKE '%華南金控%'
   OR company_name LIKE '%華南商業銀行%'
   OR company_name LIKE '%華南銀行%'
   OR company_name LIKE '%華南永昌證券%';

UPDATE jobs
SET stock_id = '2881'
WHERE company_name LIKE '%富邦金融控股%'
   OR company_name LIKE '%富邦金控%'
   OR company_name LIKE '%台北富邦銀行%'
   OR company_name LIKE '%富邦銀行%'
   OR company_name LIKE '%富邦人壽%'
   OR company_name LIKE '%富邦產險%'
   OR company_name LIKE '%富邦證券%'
   OR company_name LIKE '%富邦綜合證券%'
   OR company_name LIKE '%Fubon Financial%';

UPDATE jobs
SET stock_id = '2882'
WHERE company_name LIKE '%國泰金融控股%'
   OR company_name LIKE '%國泰金控%'
   OR company_name LIKE '%國泰世華%'
   OR company_name LIKE '%國泰人壽%'
   OR company_name LIKE '%國泰產險%'
   OR company_name LIKE '%國泰證券%'
   OR company_name LIKE '%Cathay Financial%';

UPDATE jobs
SET stock_id = '2883'
WHERE company_name LIKE '%凱基%'
   OR company_name LIKE '%凱金%'
   OR company_name LIKE '%中華開發資本%'
   OR company_name LIKE '%KGI%';

UPDATE jobs
SET stock_id = '2884'
WHERE company_name LIKE '%玉山金融控股%'
   OR company_name LIKE '%玉山金控%'
   OR company_name LIKE '%玉山商業銀行%'
   OR company_name LIKE '%玉山銀行%'
   OR company_name LIKE '%E.SUN%';

UPDATE jobs
SET stock_id = '2885'
WHERE company_name LIKE '%元大%'
   OR company_name LIKE '%Yuanta%';

UPDATE jobs
SET stock_id = '2886'
WHERE company_name LIKE '%兆豐金融控股%'
   OR company_name LIKE '%兆豐金控%'
   OR company_name LIKE '%兆豐國際商業銀行%'
   OR company_name LIKE '%兆豐銀行%'
   OR company_name LIKE '%兆豐證券%'
   OR company_name LIKE '%Mega Financial%';

UPDATE jobs
SET stock_id = '2887'
WHERE company_name LIKE '%台新新光金融控股%'
   OR company_name LIKE '%台新新光金控%'
   OR company_name LIKE '%台新銀行%'
   OR company_name LIKE '%台新證券%'
   OR company_name LIKE '%新光銀行%'
   OR company_name LIKE '%新光人壽%'
   OR company_name LIKE '%Taishin%';

UPDATE jobs
SET stock_id = '2889'
WHERE company_name LIKE '%國票金融控股%'
   OR company_name LIKE '%國票金控%'
   OR company_name LIKE '%國際票券%'
   OR company_name LIKE '%國票證券%';

UPDATE jobs
SET stock_id = '2890'
WHERE company_name LIKE '%永豐金融控股%'
   OR company_name LIKE '%永豐金控%'
   OR company_name LIKE '%永豐商業銀行%'
   OR company_name LIKE '%永豐銀行%'
   OR company_name LIKE '%永豐金證券%'
   OR company_name LIKE '%永豐證券%'
   OR company_name LIKE '%SinoPac%';

UPDATE jobs
SET stock_id = '2891'
WHERE company_name LIKE '%中信%'
   OR company_name LIKE '%中國信託%'
   OR company_name LIKE '%中國信託產物保險%'
   OR company_name LIKE '%中國信託綜合證券%'
   OR company_name LIKE '%台灣人壽%'
   OR company_name LIKE '%CTBC%';

UPDATE jobs
SET stock_id = '2892'
WHERE company_name LIKE '%第一金融控股%'
   OR company_name LIKE '%第一金控%'
   OR company_name LIKE '%第一商業銀行%'
   OR company_name LIKE '%第一銀行%'
   OR company_name LIKE '%第一金證券%';

UPDATE jobs
SET stock_id = '5880'
WHERE company_name LIKE '%合庫金融控股%'
   OR company_name LIKE '%合作金庫金融控股%'
   OR company_name LIKE '%合庫金控%'
   OR company_name LIKE '%合作金庫商業銀行%'
   OR company_name LIKE '%合作金庫銀行%'
   OR company_name LIKE '%合庫銀行%'
   OR company_name LIKE '%合庫證券%';
