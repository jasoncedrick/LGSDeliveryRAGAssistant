"""Explicit website scope/intake messages; no service facts or inferred memory.

These post-study UI checks are separate from Chapter 3's dictionary ambiguity rule.
They never choose a service, append conversational history or alter retrieval scores.
"""
import re

SERVICE = re.compile(r'\b(business|negosyo|negosyong|coffee|shop|store|stall|sari|building|balay|house|construction|occupancy|fencing|fence|signage|billboard|demolition|electrical|mechanical|plumbing|sanitary|excavat\w*|locational|zoning|cpdo|ocbo|obo|bfp|cto|fsic|fsec|fire|welding|hot.work|extinguisher|cedula|sedula|community.tax|professional.tax|ptr|real.property|amilyar|tax|treasurer|ueesz|subdivision|development.permit|occupational|employment.permit|special.permit|retire\w*|renew.*business|garbage|cenro|barangay|construction.materials|sidewalk|cooperative|corporation|online.selling|online.business|unemployed)\b', re.I)
OUTSIDE = re.compile(r"\b(passport|sss|driver.?s? licen[cs]e|weather|forecast|taxi|doctor)\b|(?:name|ngalan|pangalan).{0,25}(?:coffee|shop|business)|(?:coffee|shop|business).{0,25}(?:name ideas|naming)", re.I)
CAPABILITY = re.compile(r'(?:can you|could you|pwede|puwede).{0,45}(?:approve|book|actual application status)|(?:send|i-send|bayad|payment).{0,30}(?:here|diri|dito)|(?:here|diri|dito).{0,30}(?:send|i-send|bayad|payment)', re.I)
MESSAGES = {
 'missing': {
  'english': 'Which service is this about? Please include the permit, clearance or tax name and your full question. I process each question separately, so please repeat the details from your earlier message.',
  'taglish': 'Anong serbisyo ang tinutukoy mo? Isama ang pangalan ng permit, clearance o tax at ang buong tanong. Hiwalay kong pinoproseso ang bawat tanong, kaya pakisama ulit ang detalye mula sa naunang message.',
  'bislish': 'Unsang serbisyo imong pasabot? Iapil ang ngalan sa permit, clearance o tax ug ang tibuok pangutana. Tagsa-tagsa nako giproseso ang mga pangutana, busa palihog isulti pag-usab ang detalye sa imong naunang message.'},
 'outside': {
  'english': 'This question is outside the charter sources available here. I can help explain Business Bureau, OCBO, CPDO, BFP and City Treasurer services. Please check with the office responsible for your request.',
  'taglish': 'Hindi sakop ng mga charter source dito ang tanong na ito. Maaari kitang tulungan sa Business Bureau, OCBO, CPDO, BFP at City Treasurer services. Pakikumpirma sa opisina na may hawak ng kailangan mo.',
  'bislish': 'Dili sakop sa mga charter source dinhi ang imong pangutana. Makatabang ko sa pagpasabot sa Business Bureau, OCBO, CPDO, BFP ug City Treasurer services. Palihog pangutana sa opisina nga nagdumala sa imong kinahanglan.'},
 'capability': {
  'english': 'I can explain charter information, but this chat cannot accept payments, approve permits, book appointments or check private application records. Please name the service if you want to ask about its documented process.',
  'taglish': 'Paliwanag tungkol sa charter ang maibibigay ko. Hindi makakatanggap ng bayad, makakapag-approve ng permit, makakapag-book o makakatingin ng private application records ang chat na ito. Isama ang pangalan ng serbisyo kung gusto mong malaman ang proseso.',
  'bislish': 'Makapasabot ko sa impormasyon sa charter. Dili kini nga chat makadawat og bayad, maka-approve og permit, maka-book o makatan-aw sa private application records. Isulti ang ngalan sa serbisyo kung gusto nimong mahibalo sa proseso.'}
}


def intake_message(query, language):
    if CAPABILITY.search(query):
        return 'CAPABILITY_LIMIT', MESSAGES['capability'][language]
    naming=re.search(r'(?:name|ngalan|pangalan).{0,25}(?:coffee|shop|business)',query,re.I)
    if naming or (OUTSIDE.search(query) and not SERVICE.search(query)):
        return 'OUT_OF_SCOPE', MESSAGES['outside'][language]
    if not SERVICE.search(query):
        return 'CLARIFICATION_REQUIRED', MESSAGES['missing'][language]
    return None


def localize_clarification(prompt, language):
    options = re.findall(r'\[Option [A-Z]:\s*(.*?)\]', prompt)
    if len(options) < 2:
        return MESSAGES['missing'][language]
    intro = {'english': 'Which one do you mean?', 'taglish': 'Alin dito ang ibig mong sabihin?',
             'bislish': 'Asa niini ang imong pasabot?'}[language]
    ending = {'english': 'Please resend your full question with the specific option.',
              'taglish': 'Pakisend ulit ang buong tanong kasama ang napiling uri.',
              'bislish': 'Palihog ipadala pag-usab ang tibuok pangutana uban sa imong gipiling klase.'}[language]
    return intro + '\n' + '\n'.join(f'{i+1}. {option}' for i,option in enumerate(options)) + '\n' + ending
