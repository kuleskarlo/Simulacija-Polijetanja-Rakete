import math
import pygame, sys, numpy, os
import time

pygame.init()

#Definiranje displaya
EKRAN_VISINA, EKRAN_SIRINA = 1600, 900
EKRAN = pygame.display.set_mode((EKRAN_VISINA, EKRAN_SIRINA))
pygame.display.set_caption("Raketa-Simulacija")

clock = pygame.time.Clock()
FPS = 60

#Trošenje goriva, promjena mase, promjena stupnjeva polijetanja i poprečne površine tijekom uzlijetanja (*računa i postotak trenutnog goriva te dodaje taj podatak u listu goriva za graf)
def promjenaMaseIStupnja():
    global sila_uzgona, površina, masa, prva_promjena, druga_promjena, trenutna_masa_goriva, gorivo, ticker1, ticker2, dodana_masa, pocetna_masa_goriva
    if trenutna_masa_goriva > (maksimalna_masa_goriva - 2.04 * pow(10, 6)):
        masa = masa - prva_potrošnja_po_sekundi
        trenutna_masa_goriva -= prva_potrošnja_po_sekundi
    elif trenutna_masa_goriva <= (maksimalna_masa_goriva - 2.04 * pow(10, 6)) and prva_promjena == False:
        masa = masa - masa_prvog_stupnja
        sila_uzgona = 0
        prva_promjena = True
        ticker1 -= 1
    elif ticker1 > 0: #Tickeri su ovdje jer je razmak rada motora između prvog i drugog stadija 4 sekunde, a između trećeg i četvrtog 7 sekundi
        ticker1 -= 1
        if ticker1 == 0:
            sila_uzgona = SILA_DRUGOG_STUPNJA
    elif trenutna_masa_goriva > (maksimalna_masa_goriva - 2.468 * pow(10, 6)):
        masa = masa - druga_potrošnja_po_sekundi
        trenutna_masa_goriva -= druga_potrošnja_po_sekundi
    elif trenutna_masa_goriva <= (maksimalna_masa_goriva - 2.468 * pow(10, 6)) and druga_promjena == False:
        masa = masa - masa_drugog_stupnja
        sila_uzgona = 0
        površina = POVRŠINA_DVA
        druga_promjena = True
        ticker2 -= 1
    elif ticker2 > 0:
        ticker2 -= 1
        if ticker2 == 0:
            sila_uzgona = SILA_TREĆEG_STUPNJA
    elif trenutna_masa_goriva > 0:
        masa = masa - treća_potrošnja_po_sekundi
        trenutna_masa_goriva -= treća_potrošnja_po_sekundi
    postotak_goriva = (trenutna_masa_goriva/maksimalna_masa_goriva)*100
    gorivo.append(postotak_goriva)

#Gustoća zraka ovisno o visini - podatci preuzeti sa https://www.engineeringtoolbox.com/standard-atmosphere-d_604.html
visine = [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 15000, 20000, 25000, 30000, 40000, 50000, 60000, 70000, 80000, 100000]
gustoće = [1.225, 1.112, 1.007, 0.9093, 0.8194, 0.7364, 0.6601, 0.5900, 0.5258, 0.4671, 0.4135, 0.1948, 0.08891, 0.04008, 0.01841, 0.003996, 0.001027, 0.0003097, 0.00008283, 0.00001846, 0]
KOEFICIJENT_SILE_OTPORA_TIJELA = 0.75

#Izračunava trenutnu gustoću zraka
def gustoćaZraka(visina):
    zapravo_visina = visina + 3.05 #Dodana nadmorska visina kod Cape Carnevala
    for h in visine:
        if zapravo_visina <= h:
            pozicija = visine.index(h)
            if h <= 10000:
                koeficijent = 1000
            elif h <= 30000:
                koeficijent = 5000
            else:
                koeficijent = 10000
            omjer = (gustoće[pozicija] - gustoće[pozicija-1]) / koeficijent
            densiti = gustoće[pozicija-1] + (zapravo_visina - visine[pozicija-1])*omjer
            return densiti
    return 0

#Konstante potrebne za silu gravitacije
GRAVITACIJSKA_KONSTANTA = 6.67428*pow(10, -11)
MASA_ZEMLJE = 5.976*pow(10, 24)
RADIJUS_ZEMLJE = 6378252.531 #Udaljenost od središta Zemlje kod Cape Canaverala, SAD - glavna američka svemirska luka kod koje je većina svemirskih letjelica lansirana

#Izračunava silu gravitacije
def silaGravitacije(masa, visina):
    udaljenost = RADIJUS_ZEMLJE + visina
    greviti = (GRAVITACIJSKA_KONSTANTA * MASA_ZEMLJE * masa) / pow(udaljenost, 2)
    return greviti

#Računanje sile otpora zraka
def silaOtporaZraka(površina, gustoća_zraka, brzina):
    oz = 0.5*KOEFICIJENT_SILE_OTPORA_TIJELA*površina*gustoća_zraka*pow(brzina, 2)
    return oz

#Računanje svih sila na raketu
def zbrojSila(sila_gravitacije, sila_otpora_zraka, sila_uzgona):
    sila = sila_uzgona - (sila_gravitacije + sila_otpora_zraka)
    return sila

#Računanje brzine i visine
def računBrzine(brzina, promjena_vremena, sila, masa):
    jurić = brzina + promjena_vremena*(sila/masa)
    return jurić
def računVisine(brzina, promjena_vremena, sila, masa):
    div = brzina*promjena_vremena + 0.5*pow(promjena_vremena, 2)*(sila/masa)
    return div

#Funkcija provjerava je li uvjet istinit ili ne, ovisi o odluci igrača/onoga tko pokreće simulaciju
def provjeraUvjeta(odluka, visina, trenutna_masa_goriva):
    global uvjet
    if odluka == "A":
        uvjet = trenutna_masa_goriva > 0
    elif odluka == "B":
        uvjet = visina < 100000
    elif odluka == "C":
        uvjet = trenutna_masa_goriva > 439900
    elif odluka == "D":
        uvjet = trenutna_masa_goriva > 11900

#Klasa za gumbe
class SlikeGumbi:
    def __init__(self, slika, hover_slika, stisnuta_slika, x, y, pozicija_na_rect):
        self.slika = slika
        self.hover_slika = hover_slika
        self.stisnuta_slika = stisnuta_slika
        self.poz = (x, y)
        if pozicija_na_rect == "topleft":
            self.slika_rect = self.slika.get_rect(topleft = self.poz)
        elif pozicija_na_rect == "center":
            self.slika_rect = self.slika.get_rect(center = self.poz)
    def provjeraSudara(self, pozicija_misa):
        if pozicija_misa[0] in range(self.slika_rect.left, self.slika_rect.right) and pozicija_misa[1] in range(self.slika_rect.top, self.slika_rect.bottom):
            return True
        return False
    def crtanjeGumba(self, pozicija_misa, je_li_stisnut):
        if je_li_stisnut == True:
            EKRAN.blit(self.stisnuta_slika, self.slika_rect)
        elif pozicija_misa[0] in range(self.slika_rect.left, self.slika_rect.right) and pozicija_misa[1] in range(self.slika_rect.top, self.slika_rect.bottom):
            EKRAN.blit(self.hover_slika, self.slika_rect)
        else:
            EKRAN.blit(self.slika, self.slika_rect)
    def sliderCrtanje(self, pozicija_slajdera, je_li_stisnut, pozicija_misa):
        self.slika_rect.center = (pozicija_slajdera)
        if je_li_stisnut == True:
            EKRAN.blit(self.stisnuta_slika, self.slika_rect)
        elif pozicija_misa[0] in range(self.slika_rect.left, self.slika_rect.right) and pozicija_misa[1] in range(self.slika_rect.top, self.slika_rect.bottom):
            EKRAN.blit(self.hover_slika, self.slika_rect)
        else:
            EKRAN.blit(self.slika, self.slika_rect)

#GUI za prvi ekran (postavljanje)
outroanimacija = []
for image in range(0, 15):
    outroanimacija.append(pygame.image.load(os.path.join("Assets", "Tranzicija", f"{image}.png")).convert_alpha())
introanimacija = []
for image in range(14, -1, -1):
    introanimacija.append(pygame.image.load(os.path.join("Assets", "Tranzicija", f"{image}.png")).convert_alpha())
potpisanugovoranimacija = []
for image in range(0, 55):
    potpisanugovoranimacija.append(pygame.image.load(os.path.join("Assets", "Postavljanje", "animacija_potvrdeno", f"{image}.png")).convert_alpha())
bazapotpisanugovoranimacija = pygame.image.load(os.path.join("Assets", "Postavljanje", "animacija_potvrdeno", "baza.png")).convert_alpha()
ulaznaanimacijaugovor = []
for image in range(0, 10):
    ulaznaanimacijaugovor.append(pygame.image.load(os.path.join("Assets", "Postavljanje", "animacija_ulazna", f"{image}.png")).convert_alpha())
ugovorbaza = pygame.image.load(os.path.join("Assets", "Postavljanje", "ugovorbaza.png")).convert_alpha()
tocka = pygame.image.load(os.path.join("Assets", "Postavljanje", "tocka.png")).convert_alpha()
tockahighlight = pygame.image.load(os.path.join("Assets", "Postavljanje", "tocka_highlight.png")).convert_alpha()
tockapritisnuta = pygame.image.load(os.path.join("Assets", "Postavljanje", "tocka_pritisnuta.png")).convert_alpha()
prekrizeno = pygame.image.load(os.path.join("Assets", "Postavljanje", "prekrizeni_odgovori.png")).convert_alpha()
kvadratic = pygame.image.load(os.path.join("Assets", "Postavljanje", "uvjet.png")).convert_alpha()
kvacica = pygame.image.load(os.path.join("Assets", "Postavljanje", "kvacica.png")).convert_alpha()
uvjethover = pygame.image.load(os.path.join("Assets", "Postavljanje", "highlight_za_uvjet.png")).convert_alpha()
potvrdineaktivan = pygame.image.load(os.path.join("Assets", "Postavljanje", "potvrdi_neaktivan.png")).convert_alpha()
potvrdiidle = pygame.image.load(os.path.join("Assets", "Postavljanje", "potvrdi.png")).convert_alpha()
potvrdihover = pygame.image.load(os.path.join("Assets", "Postavljanje", "potvrdihover.png")).convert_alpha()

#Ekran za postavljanje simulacije
def main():
    global trenutna_masa_goriva, masa, dodana_masa, pocetna_masa_goriva
    run = True
    veliki_reset = True
    main_font = pygame.font.Font(os.path.join("Assets", "yoster.ttf"), 36)
    EKRAN.fill("Black")
    pygame.display.flip()
    while run:
        if veliki_reset == True: #Resetira sve potrebne varijable na početku, potrebno ako osoba odluči ponoviti simulaciju bez da ponovno pokreće kod iz fileova
            mainstart = True
            introte = 0
            ulazugo = 0
            operacijaBarbarossa = False
            barbte = 0
            izlazugo = 0
            Potvrdi = SlikeGumbi(potvrdineaktivan, potvrdihover, potvrdiidle, 890, 735, "topleft")
            Akvadrat = SlikeGumbi(kvadratic, uvjethover, kvacica, 530, 560, "center")
            Astisnut = False
            Bkvadrat = SlikeGumbi(kvadratic, uvjethover, kvacica, 530, 610, "center")
            Bstisnut = False
            Ckvadrat = SlikeGumbi(kvadratic, uvjethover, kvacica, 530, 660, "center")
            Cstisnut = False
            Conemogucen = False
            Dkvadrat = SlikeGumbi(kvadratic, uvjethover, kvacica, 530, 710, "center")
            Dstisnut = False
            Donemogucen = False
            masa_pozicija = (864, 270)
            gorivo_pozicija = (954, 410)
            MASAstisnut = False
            GORIVOstisnut = False
            MASAslajder = SlikeGumbi(tocka, tockahighlight, tockapritisnuta, masa_pozicija[0], masa_pozicija[1], "center")
            GORIVOslajder = SlikeGumbi(tocka, tockahighlight, tockapritisnuta, gorivo_pozicija[0], gorivo_pozicija[1], "center")
            veliki_reset = False
            pygame.mouse.set_visible(True)

        pozicija_misa = pygame.mouse.get_pos()

        #Lijepi pozadinu ovisno o stadiju
        if mainstart == True:
            EKRAN.blit(ulaznaanimacijaugovor[0], (0, 0))
        elif operacijaBarbarossa == True: #operacijaBarbarossa = kada se treba izvršiti završna animacija potpisivanja
            EKRAN.blit(bazapotpisanugovoranimacija, (0, 0))
        else:
            EKRAN.blit(ugovorbaza, (0, 0))

        #Crtanje slajdera za masu i gorivo
        if mainstart == True:
            pass
        else:
            if MASAstisnut == True:
                if pozicija_misa[0] < 521:
                    masa_pozicija = (521, 270)
                elif pozicija_misa[0] > 954:
                    masa_pozicija = (954, 270)
                else:
                    masa_pozicija = (pozicija_misa[0], 270)
            if GORIVOstisnut == True:
                if pozicija_misa[0] < 521:
                    gorivo_pozicija = (521, 410)
                elif pozicija_misa[0] > 954:
                    gorivo_pozicija = (954, 410)
                else:
                    gorivo_pozicija = (pozicija_misa[0], 410)
            MASAslajder.sliderCrtanje(masa_pozicija, MASAstisnut, pozicija_misa)
            GORIVOslajder.sliderCrtanje(gorivo_pozicija, GORIVOstisnut, pozicija_misa)

        #Izračunavanje sveukupne mase rakete ovisno o poziciji slajdera
        if mainstart == True:
            pass
        else:
            postotak_goriva = round(70 + ((gorivo_pozicija[0] - 521) / 433) * 30, 2)
            if postotak_goriva < 99.53:
                Donemogucen = True
                Dstisnut = False
                if postotak_goriva < 82.27:
                    Conemogucen = True
                    Cstisnut = False
                else:
                    Conemogucen = False
            else:
                Donemogucen = False
                Conemogucen = False
            trenutna_masa_goriva = maksimalna_masa_goriva * (postotak_goriva / 100)
            dodana_masa = 118000 * ((masa_pozicija[0] - 521) / 433)
            masa = masa_rakete + trenutna_masa_goriva + dodana_masa

        #Crtanje podataka o masi i postotku goriva
        if mainstart == True:
            pass
        else:
            sveukupnamasasurface = main_font.render(f"{round((masa / pow(10, 6)), 1)}", True, "#888888")
            dodanamasasurface = main_font.render(f"{round(dodana_masa, 2)}", True, "#888888")
            gorivosurface = main_font.render(f"{postotak_goriva}", True, "#888888")
            masarect = sveukupnamasasurface.get_rect(topright = (895, 165))
            dodmasarect = dodanamasasurface.get_rect(topleft = (655, 293))
            gorivorect = gorivosurface.get_rect(topright = (735, 443))
            EKRAN.blit(sveukupnamasasurface, masarect)
            EKRAN.blit(dodanamasasurface, dodmasarect)
            EKRAN.blit(gorivosurface, gorivorect)

        #Crtanje 4 kvadratića za uvjet
        if mainstart == True:
            pass
        else:
            Akvadrat.crtanjeGumba(pozicija_misa, Astisnut)
            Bkvadrat.crtanjeGumba(pozicija_misa, Bstisnut)
            if Conemogucen == True:
                EKRAN.blit(prekrizeno, (515, 645))
                Cstisnut = False
            else:
                Ckvadrat.crtanjeGumba(pozicija_misa, Cstisnut)
            if Donemogucen == True:
                EKRAN.blit(prekrizeno, (515, 695))
                Dstisnut = False
            else:
                Dkvadrat.crtanjeGumba(pozicija_misa, Dstisnut)
        
        #Crtanje gumba za potvrditi
        if mainstart == True or operacijaBarbarossa == True:
            pass
        else:
            if Astisnut or Bstisnut or Cstisnut or Dstisnut:
                if Potvrdi.provjeraSudara(pozicija_misa):
                    EKRAN.blit(Potvrdi.hover_slika, Potvrdi.slika_rect)
                else:
                    EKRAN.blit(Potvrdi.stisnuta_slika, Potvrdi.slika_rect)
            else:
                EKRAN.blit(Potvrdi.slika, Potvrdi.slika_rect)

        if mainstart == True: #Ulazna animacija
            if introte < 15:
                EKRAN.blit(introanimacija[int(introte)], (0, 0))
                introte += 0.23
            if introte >= 15:
                EKRAN.blit(ulaznaanimacijaugovor[int(ulazugo)], (0, 0))
                ulazugo += 0.25
                if ulazugo >= 10:
                    mainstart = False
                    introte = 0
                    ulazugo = 0

        if operacijaBarbarossa == True: #Završna animacija potpisivanja
            if barbte < 55:
                EKRAN.blit(potpisanugovoranimacija[int(barbte)], (0, 0))
                barbte += 0.16
            if barbte >= 55:
                EKRAN.blit(potpisanugovoranimacija[54], (0, 0))
                EKRAN.blit(outroanimacija[int(izlazugo)], (0, 0))
                izlazugo += 0.23
                if izlazugo >= 15:
                    operacijaBarbarossa = False
                    barbte = 0
                    izlazugo = 0
                    pocetna_masa_goriva = trenutna_masa_goriva
                    simulacija2(odluka)
                    veliki_reset = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if operacijaBarbarossa == True:
                    pass
                else:
                    if Akvadrat.provjeraSudara(pozicija_misa):
                        Astisnut = True
                        Bstisnut = False
                        Cstisnut = False
                        Dstisnut = False
                    if Bkvadrat.provjeraSudara(pozicija_misa):
                        Astisnut = False
                        Bstisnut = True
                        Cstisnut = False
                        Dstisnut = False
                    if Conemogucen == False:
                        if Ckvadrat.provjeraSudara(pozicija_misa):
                            Astisnut = False
                            Bstisnut = False
                            Cstisnut = True
                            Dstisnut = False
                    if Donemogucen == False:
                        if Dkvadrat.provjeraSudara(pozicija_misa):
                            Astisnut = False
                            Bstisnut = False
                            Cstisnut = False
                            Dstisnut = True
                    if MASAslajder.provjeraSudara(pozicija_misa):
                        if GORIVOstisnut == False:
                            MASAstisnut = True
                    if GORIVOslajder.provjeraSudara(pozicija_misa):
                        if MASAstisnut == False:
                            GORIVOstisnut = True
                    if Potvrdi.provjeraSudara(pozicija_misa):
                        if Astisnut or Bstisnut or Cstisnut or Dstisnut:
                            if Astisnut:
                                odluka = "A"
                            elif Bstisnut:
                                odluka = "B"
                            elif Cstisnut:
                                odluka = "C"
                            elif Dstisnut:
                                odluka = "D"
                            operacijaBarbarossa = True
                        else:
                            pass
            if event.type == pygame.MOUSEBUTTONUP:
                if operacijaBarbarossa == True:
                    pass
                else:
                    if MASAstisnut == True:
                        MASAstisnut = False
                    if GORIVOstisnut == True:
                        GORIVOstisnut = False
        pygame.display.update()
        clock.tick(FPS)

#GUI za drugi ekran (simulacija)
pozadinaplanetaanimacija = []
for image in range(0, 20):
    pozadinaplanetaanimacija.append(pygame.image.load(os.path.join("Assets", "Simulacija", f"pozadina{image}.png")).convert_alpha())
ekranokvirianimacija = []
for image in range(0, 3):
    ekranokvirianimacija.append(pygame.image.load(os.path.join("Assets", "Simulacija", f"okvirekran{image + 1}.png")).convert_alpha())
promjenaekranaanimacija = []
for image in range(0, 27):
    promjenaekranaanimacija.append(pygame.image.load(os.path.join("Assets", "Simulacija", f"promjenagrafa{image}.png")).convert_alpha())
raketablinkanje = []
for image in range(0, 2):
    raketablinkanje.append(pygame.image.load(os.path.join("Assets", "Simulacija", f"raketa{image}.png")).convert_alpha())
raketahover = pygame.image.load(os.path.join("Assets", "Simulacija", f"raketahover.png")).convert_alpha()
raketainfo = pygame.image.load(os.path.join("Assets", "Simulacija", f"raketa_info.png")).convert_alpha()
vrijemex1 = pygame.image.load(os.path.join("Assets", "Simulacija", f"x1.png")).convert_alpha()
vrijemex2 = pygame.image.load(os.path.join("Assets", "Simulacija", f"x2.png")).convert_alpha()
vrijemex3 = pygame.image.load(os.path.join("Assets", "Simulacija", f"x3.png")).convert_alpha()
vrijemex5 = pygame.image.load(os.path.join("Assets", "Simulacija", f"x5.png")).convert_alpha()
vrijemex10 = pygame.image.load(os.path.join("Assets", "Simulacija", f"x10.png")).convert_alpha()
uspjesanekran = pygame.image.load(os.path.join("Assets", "Simulacija", f"uspjesno.png")).convert_alpha()
bezuspjesanekran = pygame.image.load(os.path.join("Assets", "Simulacija", f"bezuspjesno.png")).convert_alpha()
izadigumb = pygame.image.load(os.path.join("Assets", "Simulacija", f"izadi.png")).convert_alpha()
izadigumbhover = pygame.image.load(os.path.join("Assets", "Simulacija", f"izadihover.png")).convert_alpha()
pauziranovrijeme = pygame.image.load(os.path.join("Assets", "Simulacija", f"pauzirano_vrijeme.png")).convert_alpha()
playidle = pygame.image.load(os.path.join("Assets", "Simulacija", f"idleplay.png")).convert_alpha()
playhover = pygame.image.load(os.path.join("Assets", "Simulacija", f"hoverplay.png")).convert_alpha()
playpritisnuto = pygame.image.load(os.path.join("Assets", "Simulacija", f"pritisnutoplay.png")).convert_alpha()
pauseidle = pygame.image.load(os.path.join("Assets", "Simulacija", f"idlepause.png")).convert_alpha()
pausehover = pygame.image.load(os.path.join("Assets", "Simulacija", f"hoverpause.png")).convert_alpha()
pausepritisnuto = pygame.image.load(os.path.join("Assets", "Simulacija", f"pritisnutopause.png")).convert_alpha()
nextidle = pygame.image.load(os.path.join("Assets", "Simulacija", f"idlenext.png")).convert_alpha()
nexthover = pygame.image.load(os.path.join("Assets", "Simulacija", f"hovernext.png")).convert_alpha()
nextpritisnuto = pygame.image.load(os.path.join("Assets", "Simulacija", f"pritisnutonext.png")).convert_alpha()
backidle = pygame.image.load(os.path.join("Assets", "Simulacija", f"idleback.png")).convert_alpha()
backhover = pygame.image.load(os.path.join("Assets", "Simulacija", f"hoverback.png")).convert_alpha()
backpritisnuto = pygame.image.load(os.path.join("Assets", "Simulacija", f"pritisnutoback.png")).convert_alpha()
visinaidle = pygame.image.load(os.path.join("Assets", "Simulacija", f"idlevisina.png")).convert_alpha()
visinahover = pygame.image.load(os.path.join("Assets", "Simulacija", f"hovervisina.png")).convert_alpha()
visinapritisnuto = pygame.image.load(os.path.join("Assets", "Simulacija", f"pritisnutovisina.png")).convert_alpha()
brzinaidle = pygame.image.load(os.path.join("Assets", "Simulacija", f"idlebrzina.png")).convert_alpha()
brzinahover = pygame.image.load(os.path.join("Assets", "Simulacija", f"hoverbrzina.png")).convert_alpha()
brzinapritisnuto = pygame.image.load(os.path.join("Assets", "Simulacija", f"pritisnutobrzina.png")).convert_alpha()
gorivoidle = pygame.image.load(os.path.join("Assets", "Simulacija", f"idlegorivo.png")).convert_alpha()
gorivohover = pygame.image.load(os.path.join("Assets", "Simulacija", f"hovergorivo.png")).convert_alpha()
gorivopritisnuto = pygame.image.load(os.path.join("Assets", "Simulacija", f"pritisnutogorivo.png")).convert_alpha()
masaidle = pygame.image.load(os.path.join("Assets", "Simulacija", f"idlemasa.png")).convert_alpha()
masahover = pygame.image.load(os.path.join("Assets", "Simulacija", f"hovermasa.png")).convert_alpha()
masapritisnuto = pygame.image.load(os.path.join("Assets", "Simulacija", f"pritisnutomasa.png")).convert_alpha()

#NASA Saturn V raketa https://en.wikipedia.org/wiki/Saturn_V
masa_rakete = 196600 #Masa svih stadija i masa elektroničkih instrumenata kojima su austronauti upravljali raketom
maksimalna_masa_goriva = 2479900
POVRŠINA_JEDAN = pow(5, 2)*math.pi #Površina tijekom prvog i drugog stupnja uzlijetanja
POVRŠINA_DVA = pow(3.302, 2)*math.pi #Površina tijekom trećeg stupnja uzlijetanja

#Sile, mase i potrošnja goriva tijekom raznih stupnjeva polijetanja https://www.mnealon.eosc.edu/RocketSciencePage5.htm
SILA_PRVOG_STUPNJA = 33.4*pow(10, 6)
prva_potrošnja_po_sekundi = 13600
masa_prvog_stupnja = 0.136*pow(10, 6)
SILA_DRUGOG_STUPNJA = 4.46*pow(10, 6)
druga_potrošnja_po_sekundi = 1185.595568
masa_drugog_stupnja = 0.0432*pow(10, 6)
SILA_TREĆEG_STUPNJA = pow(10, 6)
treća_potrošnja_po_sekundi = 24.9475891

#Ekran same simulacije
def simulacija2(odluka):
    global sila_uzgona, površina, masa, prva_promjena, druga_promjena, trenutna_masa_goriva, gorivo, ticker1, ticker2, visina, brzina, runtime, tejedan

    run = True

    EKRAN.fill("Black")
    pygame.display.flip()

    #Postavljanje početnih vrijednosti
    visina = 55.3
    brzina = 0
    površina = POVRŠINA_JEDAN
    gustoća_zraka = 1,295
    sila_uzgona = SILA_PRVOG_STUPNJA

    #Liste potrebne za izradu grafova
    vrijeme = [0]
    sekunde = 0
    heights = [visina]
    visine_graf = [(visina / 1000)]
    brzine = [0]
    lista_masa = [(masa / 1000)]
    gorivo = [100]

    #Varijable za provedbu simulacije
    prva_promjena = False
    druga_promjena = False
    ticker1 = 3
    ticker2 = 6

    #Provedba simulacije i zapisivanje podataka u liste koje će služiti za prikaz podataka na ekran
    provjeraUvjeta(odluka, visina, trenutna_masa_goriva)
    while uvjet:
        gravitacija = silaGravitacije(masa, visina)
        gustoća_zraka = gustoćaZraka(visina)
        otpor_zraka = silaOtporaZraka(površina, gustoća_zraka, brzina)
        ukupna_sila = zbrojSila(gravitacija, otpor_zraka, sila_uzgona)
        visina += računVisine(brzina, 1, ukupna_sila, masa)
        brzina = računBrzine(brzina, 1, ukupna_sila, masa)
        promjenaMaseIStupnja()
        sekunde += 1
        lista_masa.append(round((masa / 1000), 2))
        brzine.append((brzina / 3.6))
        vrijeme.append(sekunde)
        heights.append((visina))
        visine_graf.append((visina / 1000))
        provjeraUvjeta(odluka, visina, trenutna_masa_goriva)
        if brzina <= 0:
            break

    #Setup svih varijabli, grafova i gumbova potrebnih za prikazivanje na ekranu
    runtime = False
    simulacijajegotova = False
    sveukupno_vrijeme = 0
    ubrzanje = 1

    visinegraf = Graf("visina[km]", "vrijeme[s]", visine_graf, vrijeme)
    brzinegraf = Graf("brzina[km/h]", "vrijeme[s]", brzine, vrijeme)
    gorivograf = Graf("gorivo[%]", "vrijeme[s]", gorivo, vrijeme)
    masagraf = Graf("masa[t]", "vrijeme[s]", lista_masa, vrijeme)

    Gback = SlikeGumbi(backidle, backhover, backpritisnuto, 20, 815, "topleft")
    Gbackpritisnuto = False
    Gplay = SlikeGumbi(playidle, playhover, playpritisnuto, 130, 815, "topleft")
    Gplaypritisnuto = False
    Gpause = SlikeGumbi(pauseidle, pausehover, pausepritisnuto, 240, 815, "topleft")
    Gpausepritisnuto = True
    Gnext = SlikeGumbi(nextidle, nexthover, nextpritisnuto, 350, 815, "topleft")
    Gnextpritisnuto = False

    Gvisina = SlikeGumbi(visinaidle, visinahover, visinapritisnuto, 830, 825, "topleft")
    Gvisinapritisnuto = True
    Gbrzina = SlikeGumbi(brzinaidle, brzinahover, brzinapritisnuto, 1025, 825, "topleft")
    Gbrzinapritisnuto = False
    Ggorivo = SlikeGumbi(gorivoidle, gorivohover, gorivopritisnuto, 1215, 825, "topleft")
    Ggorivopritisnuto = False
    Gmasa = SlikeGumbi(masaidle, masahover, masapritisnuto, 1405, 825, "topleft")
    Gmasapritisnuto = False

    animacija_ciklona = 0
    animacija_ekrani = 0
    animacija_raketa = 0
    animacija_promjene_ekrana = False
    index_za_switch = 0
    izadi_anim = False
    izlazugo = 0
    ulaznaanimacija = True
    introte = 0

    pygame.mouse.set_visible(True)

    while run == True:

        pozicija_misa = pygame.mouse.get_pos()

        if int(sveukupno_vrijeme) >= sekunde: #Provjera je li simulacija završila
            runtime = False
            simulacijajegotova = True

        #Animacija pozadine
        EKRAN.blit(pozadinaplanetaanimacija[int(animacija_ciklona)], (0, 0))
        if runtime == True:
            animacija_ciklona += (0.01 * ubrzanje)
            if animacija_ciklona >= 20:
                animacija_ciklona = 0

        #Prikazivanje ekrana
        EKRAN.blit(ekranokvirianimacija[int(animacija_ekrani)], (0, 0))
        animacija_ekrani += 0.025
        if animacija_ekrani >= 3:
            animacija_ekrani = 0

        #Crtanje grafa ovisno o pritisnutom gumbu
        if Gvisinapritisnuto == True:
            visinegraf.crtanjeGrafa((910, 730), sveukupno_vrijeme)
            gledanje_grafa(pozicija_misa, (910, 730), sveukupno_vrijeme, visine_graf, "km")
        elif Gbrzinapritisnuto == True:
            brzinegraf.crtanjeGrafa((910, 730), sveukupno_vrijeme)
            gledanje_grafa(pozicija_misa, (910, 730), sveukupno_vrijeme, brzine, "km/h")
        elif Ggorivopritisnuto == True:
            gorivograf.crtanjeGrafa((910, 730), sveukupno_vrijeme)
            gledanje_grafa(pozicija_misa, (910, 730), sveukupno_vrijeme, gorivo, "%")
        elif Gmasapritisnuto == True:
            masagraf.crtanjeGrafa((910, 730), sveukupno_vrijeme)
            gledanje_grafa(pozicija_misa, (910, 730), sveukupno_vrijeme, lista_masa, "t")

        #Crtanje rakete
        raketa_rect = raketablinkanje[0].get_rect(center = (int(232 + math.cos(0.895663363) * ((visine_graf[int(sveukupno_vrijeme)] / 8154.37) * 796.8)), int(672 - math.sin(0.895663363) * ((visine_graf[int(sveukupno_vrijeme)] / 8154.37) * 796.8))))
        EKRAN.blit(raketablinkanje[int(animacija_raketa)], raketa_rect)
        animacija_raketa += 0.1
        if animacija_raketa >= 2:
            animacija_raketa = 0
        if pozicija_misa[0] in range(raketa_rect.left, raketa_rect.right) and pozicija_misa[1] in range(raketa_rect.top, raketa_rect.bottom):
            pozicijainfo = raketa_rect.topleft
            pozin = (pozicijainfo[0] - 70, pozicijainfo[1] - 30)
            EKRAN.blit(raketainfo, pozin)

        #Animacija promjene grafa na ekranu
        if animacija_promjene_ekrana == True:
            EKRAN.blit(promjenaekranaanimacija[int(index_za_switch)], (0, 0))
            index_za_switch += 1
            if index_za_switch >= 27:
                index_za_switch = 0
                animacija_promjene_ekrana = False

        #Svi podatci prikazani na ekranima
        podatak_u_gornjem_lijevom_kutu(205, 10, visine_graf, "km", sveukupno_vrijeme)
        podatak_u_gornjem_lijevom_kutu(205, 74, brzine, "kmh", sveukupno_vrijeme)
        podatak_u_gornjem_lijevom_kutu(205, 130, gorivo, f"prcnt", sveukupno_vrijeme)

        crtanjeUbrzanja(ubrzanje)
        
        sveukupno_vrijeme += racunanje_vremena(ubrzanje, runtime)
        if int(sveukupno_vrijeme) >= sekunde:
            sveukupno_vrijeme = sekunde
        stoperica(sveukupno_vrijeme, 792, 836)

        #Gumbi
        Gback.crtanjeGumba(pozicija_misa, Gbackpritisnuto)
        Gplay.crtanjeGumba(pozicija_misa, Gplaypritisnuto)
        Gpause.crtanjeGumba(pozicija_misa, Gpausepritisnuto)
        Gnext.crtanjeGumba(pozicija_misa, Gnextpritisnuto)
        Gvisina.crtanjeGumba(pozicija_misa, Gvisinapritisnuto)
        Gbrzina.crtanjeGumba(pozicija_misa, Gbrzinapritisnuto)
        Ggorivo.crtanjeGumba(pozicija_misa, Ggorivopritisnuto)
        Gmasa.crtanjeGumba(pozicija_misa, Gmasapritisnuto)

        if simulacijajegotova == True: #Crtanje završnog ekrana ako je simulacija završila
            if odluka == "B":
                if visine_graf[-1] < 100:
                    EKRAN.blit(bezuspjesanekran, (0, 0))
                else:
                    EKRAN.blit(uspjesanekran, (0, 0))
                    izadi_rect = izadigumb.get_rect(topleft = (350, 455))
                    if pozicija_misa[0] in range(izadi_rect.left, izadi_rect.right) and pozicija_misa[1] in range(izadi_rect.top, izadi_rect.bottom):
                        EKRAN.blit(izadigumbhover, izadi_rect)
                    else:
                        EKRAN.blit(izadigumb, izadi_rect)
            else:
                EKRAN.blit(uspjesanekran, (0, 0))
                izadi_rect = izadigumb.get_rect(topleft = (350, 455))
                if pozicija_misa[0] in range(izadi_rect.left, izadi_rect.right) and pozicija_misa[1] in range(izadi_rect.top, izadi_rect.bottom):
                    EKRAN.blit(izadigumbhover, izadi_rect)
                else:
                    EKRAN.blit(izadigumb, izadi_rect)
        elif runtime == False:
            EKRAN.blit(pauziranovrijeme, (0, 0))

        #Animacija za početak i kraj simulacije
        if izadi_anim == True:
            EKRAN.blit(outroanimacija[int(izlazugo)], (0, 0))
            izlazugo += 0.23
            if izlazugo >= 15:
                return None          
        if ulaznaanimacija == True:
            EKRAN.blit(introanimacija[int(introte)], (0, 0))
            introte += 0.23
            if introte >= 15:
                ulaznaanimacija = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if simulacijajegotova == True: #Provjera za izađi gumb ako je simulacija gotova
                    if pozicija_misa[0] in range(izadi_rect.left, izadi_rect.right) and pozicija_misa[1] in range(izadi_rect.top, izadi_rect.bottom):
                        izadi_anim = True
                else:
                    if Gplay.provjeraSudara(pozicija_misa):
                        if runtime:
                            pass
                        else:
                            runtime = True
                            Gplaypritisnuto = True
                            Gpausepritisnuto = False
                            tejedan = time.time()
                    if Gpause.provjeraSudara(pozicija_misa):
                        if runtime:
                            runtime = False
                            Gplaypritisnuto = False
                            Gpausepritisnuto = True
                        else:
                            pass
                if Gnext.provjeraSudara(pozicija_misa):
                    Gnextpritisnuto = True
                    if ubrzanje == 1:
                        ubrzanje = 2
                    elif ubrzanje == 2:
                        ubrzanje = 3
                    elif ubrzanje == 3:
                        ubrzanje = 5
                    elif ubrzanje == 5:
                        ubrzanje = 10
                    else:
                        pass
                if Gback.provjeraSudara(pozicija_misa):
                    Gbackpritisnuto = True
                    if ubrzanje == 10:
                        ubrzanje = 5
                    elif ubrzanje == 5:
                        ubrzanje = 3
                    elif ubrzanje == 3:
                        ubrzanje = 2
                    elif ubrzanje == 2:
                        ubrzanje = 1
                    else:
                        pass
                if Gvisina.provjeraSudara(pozicija_misa):
                    if Gvisinapritisnuto == True or animacija_promjene_ekrana == True:
                        pass
                    else:
                        animacija_promjene_ekrana = True
                        Gvisinapritisnuto = True
                        Gbrzinapritisnuto = False
                        Ggorivopritisnuto = False
                        Gmasapritisnuto = False
                if Gbrzina.provjeraSudara(pozicija_misa):
                    if Gbrzinapritisnuto == True or animacija_promjene_ekrana == True:
                        pass
                    else:
                        animacija_promjene_ekrana = True
                        Gvisinapritisnuto = False
                        Gbrzinapritisnuto = True
                        Ggorivopritisnuto = False
                        Gmasapritisnuto = False
                if Ggorivo.provjeraSudara(pozicija_misa):
                    if Ggorivopritisnuto == True or animacija_promjene_ekrana == True:
                        pass
                    else:
                        animacija_promjene_ekrana = True
                        Gvisinapritisnuto = False
                        Gbrzinapritisnuto = False
                        Ggorivopritisnuto = True
                        Gmasapritisnuto = False
                if Gmasa.provjeraSudara(pozicija_misa):
                    if Gmasapritisnuto == True or animacija_promjene_ekrana == True:
                        pass
                    else:
                        animacija_promjene_ekrana = True
                        Gvisinapritisnuto = False
                        Gbrzinapritisnuto = False
                        Ggorivopritisnuto = False
                        Gmasapritisnuto = True

            if event.type == pygame.MOUSEBUTTONUP:
                if Gnextpritisnuto == True:
                    Gnextpritisnuto = False
                if Gbackpritisnuto == True:
                    Gbackpritisnuto = False


        pygame.display.update()
        clock.tick(FPS)


class Graf():
    def __init__(self, y_os_naziv, x_os_naziv, y_lista, x_lista):
        self.apscisa = x_os_naziv
        self.oordinata = y_os_naziv
        self.x_vrijednosti = x_lista
        self.y_vrijednosti = y_lista
    def crtanjeGrafa(self, pozicija_ishodista, vrijeme_simulacije):
        grafFONT = pygame.font.Font(None, 25)
        #Crtanje imena x i y osi (npr. vrijeme[s])
        grafx_surface = grafFONT.render(f"{self.apscisa}", False, "#315518", None)
        grafx_rect = grafx_surface.get_rect(center = (pozicija_ishodista[0] + 605, pozicija_ishodista[1] + 30))
        grafy_surface = grafFONT.render(f"{self.oordinata}", False, "#315518", None)
        grafy_rect = grafy_surface.get_rect(topleft = (pozicija_ishodista[0] - 65, pozicija_ishodista[1] - 585))
        EKRAN.blit(grafx_surface, grafx_rect)
        EKRAN.blit(grafy_surface, grafy_rect)
        #Crtanje strelica
        pygame.draw.line(EKRAN, "#315518", pozicija_ishodista, (pozicija_ishodista[0], pozicija_ishodista[1] - 555), 6)
        pygame.draw.line(EKRAN, "#315518", pozicija_ishodista, (pozicija_ishodista[0] + 555, pozicija_ishodista[1]), 6)
        pygame.draw.polygon(EKRAN, "#315518", [(pozicija_ishodista[0], pozicija_ishodista[1] - (555 + 10)), (pozicija_ishodista[0] + 7, pozicija_ishodista[1] - 555), (pozicija_ishodista[0] - 7, pozicija_ishodista[1] - 555)])
        pygame.draw.polygon(EKRAN, "#315518", [(pozicija_ishodista[0] + (555 + 10), pozicija_ishodista[1]), (pozicija_ishodista[0] + 555, pozicija_ishodista[1] - 7), (pozicija_ishodista[0] + 555, pozicija_ishodista[1] + 7)])
        font = pygame.font.Font(None, 20)
        #Crtanje manjih crtica za varijable
        vreme_simulacije = int(vrijeme_simulacije)
        if vreme_simulacije == 0:
            pass
        elif vreme_simulacije < 10:
            pomak = int(550 / vreme_simulacije)
            zadnji = pomak
            pygame.draw.line(EKRAN, "#315518", (pozicija_ishodista[0] + 4, pozicija_ishodista[1] - 550), (pozicija_ishodista[0] - 4, pozicija_ishodista[1] - 550), 4)
            tekst_surface = font.render(f"{round(max(self.y_vrijednosti[0:(vreme_simulacije + 1)]), 2)}", False, "#315518", None)
            tekst_rect = tekst_surface.get_rect(center = (pozicija_ishodista[0] - 30, pozicija_ishodista[1] - 550))
            EKRAN.blit(tekst_surface, tekst_rect)
            if self.y_vrijednosti[0] != max(self.y_vrijednosti):
                if vreme_simulacije > 4:
                    pygame.draw.line(EKRAN, "#315518", (pozicija_ishodista[0] + 4, pozicija_ishodista[1] - int(550*(self.y_vrijednosti[0] / max(self.y_vrijednosti[0:(vreme_simulacije + 1)])))), (pozicija_ishodista[0] - 4, pozicija_ishodista[1] - int(550*(self.y_vrijednosti[0] / self.y_vrijednosti[vreme_simulacije]))), 4)
                    tekst_surface = font.render(f"{round(self.y_vrijednosti[0], 2)}", False, "#315518", None)
                    tekst_rect = tekst_surface.get_rect(center = (pozicija_ishodista[0] - 30, pozicija_ishodista[1] - int(550*(self.y_vrijednosti[0] / max(self.y_vrijednosti[0:(vreme_simulacije + 1)])))))
                    EKRAN.blit(tekst_surface, tekst_rect)
            for i in range(0, vreme_simulacije):
                pygame.draw.line(EKRAN, "#315518", (pozicija_ishodista[0] + zadnji, pozicija_ishodista[1] + 4), (pozicija_ishodista[0] + zadnji, pozicija_ishodista[1] - 4), 4)
                tekst_surface = font.render(f"{i + 1}", False, "#315518", None)
                tekst_rect = tekst_surface.get_rect(center = (pozicija_ishodista[0] + zadnji, pozicija_ishodista[1] + 15))
                EKRAN.blit(tekst_surface, tekst_rect)
                zadnji += pomak
            zadnja_pozicija = (pozicija_ishodista[0], pozicija_ishodista[1] - int(550*(self.y_vrijednosti[0] / max(self.y_vrijednosti[0:(vreme_simulacije + 1)]))))
            #Crtanje osi na grafu
            zadnji = pomak
            for i in range(0, vreme_simulacije):
                pygame.draw.line(EKRAN, "#315518", zadnja_pozicija, (pozicija_ishodista[0] + zadnji, pozicija_ishodista[1] - int((550*(self.y_vrijednosti[i + 1] / max(self.y_vrijednosti[0:(vreme_simulacije + 1)]))))), 4)
                zadnja_pozicija = (pozicija_ishodista[0] + zadnji, pozicija_ishodista[1] - int((550*(self.y_vrijednosti[i + 1] / max(self.y_vrijednosti[0:(vreme_simulacije + 1)])))))
                zadnji += pomak
        #Crtanje manjih crtica za varijable
        elif vreme_simulacije >= 10:
            pomak = 55
            zadnji = pomak
            pygame.draw.line(EKRAN, "#315518", (pozicija_ishodista[0] + 4, pozicija_ishodista[1] - 550), (pozicija_ishodista[0] - 4, pozicija_ishodista[1] - 550), 4)
            tekst_surface = font.render(f"{round(max(self.y_vrijednosti[0:(vreme_simulacije + 1)]), 2)}", False, "#315518", None)
            tekst_rect = tekst_surface.get_rect(center = (pozicija_ishodista[0] - 30, pozicija_ishodista[1] - 550))
            EKRAN.blit(tekst_surface, tekst_rect)
            if self.y_vrijednosti[0] != max(self.y_vrijednosti):
                if vreme_simulacije > 4:
                    pygame.draw.line(EKRAN, "#315518", (pozicija_ishodista[0] + 4, pozicija_ishodista[1] - int(550*(self.y_vrijednosti[0] / self.y_vrijednosti[vreme_simulacije]))), (pozicija_ishodista[0] - 4, pozicija_ishodista[1] - int(550*(self.y_vrijednosti[0] / self.y_vrijednosti[vreme_simulacije]))), 4)
                    tekst_surface = font.render(f"{round(self.y_vrijednosti[0], 2)}", False, "#315518", None)
                    tekst_rect = tekst_surface.get_rect(center = (pozicija_ishodista[0] - 30, pozicija_ishodista[1] - int(550*(self.y_vrijednosti[0] / self.y_vrijednosti[vreme_simulacije]))))
                    EKRAN.blit(tekst_surface, tekst_rect)
            for i in range(0, 10):
                pygame.draw.line(EKRAN, "#315518", (pozicija_ishodista[0] + zadnji, pozicija_ishodista[1] + 4), (pozicija_ishodista[0] + zadnji, pozicija_ishodista[1] - 4), 4)
                tekst_surface = font.render(f"{int((vreme_simulacije / 10)*(i + 1))}", False, "#315518", None)
                tekst_rect = tekst_surface.get_rect(center = (pozicija_ishodista[0] + zadnji, pozicija_ishodista[1] + 15))
                EKRAN.blit(tekst_surface, tekst_rect)
                zadnji += pomak
            zadnja_pozicija = (pozicija_ishodista[0], pozicija_ishodista[1] - int(550*(self.y_vrijednosti[0] / max(self.y_vrijednosti[0:(vreme_simulacije + 1)]))))
            #Crtanje osi na grafu
            if vreme_simulacije >= 275:
                broj_tocaka = 275
                pomak = 2
            elif vreme_simulacije >= 110:
                broj_tocaka = 110
                pomak = 5
            elif vreme_simulacije >= 55:
                broj_tocaka = 55
                pomak = 10
            elif vreme_simulacije >= 22:
                broj_tocaka = 22
                pomak = 25
            else:
                broj_tocaka = 10
                pomak = 55
            zadnji = pomak
            for i in range(0, broj_tocaka):
                pygame.draw.line(EKRAN, "#315518", zadnja_pozicija, (pozicija_ishodista[0] + zadnji, pozicija_ishodista[1] - int((550*(self.y_vrijednosti[int((i + 1)*(vreme_simulacije / broj_tocaka))] / max(self.y_vrijednosti[0:(vreme_simulacije + 1)]))))), 4)
                zadnja_pozicija = (pozicija_ishodista[0] + zadnji, pozicija_ishodista[1] - int((550*(self.y_vrijednosti[int((i + 1)*(vreme_simulacije / broj_tocaka))] / max(self.y_vrijednosti[0:(vreme_simulacije + 1)])))))
                zadnji += pomak

def crtanjeUbrzanja(kolicnik):
    if kolicnik == 1:
        EKRAN.blit(vrijemex1, (0, 0))
    elif kolicnik == 2:
        EKRAN.blit(vrijemex2, (0, 0))
    elif kolicnik == 3:
        EKRAN.blit(vrijemex3, (0, 0))
    elif kolicnik == 5:
        EKRAN.blit(vrijemex5, (0, 0))
    elif kolicnik == 10:
        EKRAN.blit(vrijemex10, (0, 0))

def racunanje_vremena(količnik, runtime):
    global tejedan
    if runtime:
        delta = (time.time() - tejedan)*količnik
        tejedan = time.time()
        return delta
    else:
        return 0

def stoperica(vrijeme, pozicija_x, pozicija_y):
    font = pygame.font.Font(os.path.join("Assets", "yoster.ttf"), 50)
    stoperica_surf = font.render(f"{round(vrijeme, 3)}s", False, 'White')
    stoperica_rect = stoperica_surf.get_rect(topright = (pozicija_x, pozicija_y))
    EKRAN.blit(stoperica_surf, stoperica_rect)

def podatak_u_gornjem_lijevom_kutu(posx, posy, lista_podatka, mjerna_jedinica, sveukupno_vrijeme):
    font = pygame.font.Font(os.path.join("Assets", "yoster.ttf"), 26)
    podatak_surface = font.render(f"{round(lista_podatka[int(sveukupno_vrijeme)], 3)}" + mjerna_jedinica, True, "White")
    podatak_rectangle = podatak_surface.get_rect(topright = (posx, posy))
    EKRAN.blit(podatak_surface, podatak_rectangle)

def draw_line_dashed(surface, color, start_pos, end_pos, width = 1, dash_length = 10, exclude_corners = True): #Preuzeto sa stackoverflowa, crta crvene iscrtkane linije tijekom gledanja grafa

    # convert tuples to numpy arrays
    start_pos = numpy.array(start_pos)
    end_pos   = numpy.array(end_pos)

    # get euclidian distance between start_pos and end_pos
    length = numpy.linalg.norm(end_pos - start_pos)

    # get amount of pieces that line will be split up in (half of it are amount of dashes)
    dash_amount = int(length / dash_length)

    # x-y-value-pairs of where dashes start (and on next, will end)
    dash_knots = numpy.array([numpy.linspace(start_pos[i], end_pos[i], dash_amount) for i in range(2)]).transpose()

    return [pygame.draw.line(surface, color, tuple(dash_knots[n]), tuple(dash_knots[n+1]), width)
            for n in range(int(exclude_corners), dash_amount - int(exclude_corners), 2)]

def gledanje_grafa(pozicija_misa, pozicija_ishodista_grafa, vrijeme, y_lista, mjerna_jedinica):
    if vrijeme == 0:
        pass
    elif pozicija_misa[0] in range(840, 1575) and pozicija_misa[1] in range(135, 785):
        pygame.mouse.set_visible(False)    
        draw_line_dashed(EKRAN, "#C54640", (pozicija_ishodista_grafa[0], pozicija_ishodista_grafa[1] - (550*(y_lista[int(vrijeme * ((pozicija_misa[0] - 840) / 735))] / max(y_lista[0:int(vrijeme)])))), (pozicija_ishodista_grafa[0] + 550 * ((pozicija_misa[0] - 840) / 735), pozicija_ishodista_grafa[1] - (550*(y_lista[int(vrijeme * ((pozicija_misa[0] - 840) / 735))] / max(y_lista[0:int(vrijeme)])))), width=2, dash_length=5)
        draw_line_dashed(EKRAN, "#C54640", (pozicija_ishodista_grafa[0] + 550 * ((pozicija_misa[0] - 840) / 735), pozicija_ishodista_grafa[1]), (pozicija_ishodista_grafa[0] + 550 * ((pozicija_misa[0] - 840) / 735), pozicija_ishodista_grafa[1] - (550*(y_lista[int(vrijeme * ((pozicija_misa[0] - 840) / 735))] / max(y_lista[0:int(vrijeme)])))), width=2, dash_length=5)
        pygame.draw.circle(EKRAN, "#C54640", (pozicija_ishodista_grafa[0] + 550 * ((pozicija_misa[0] - 840) / 735), pozicija_ishodista_grafa[1] - (550*(y_lista[int(vrijeme * ((pozicija_misa[0] - 840) / 735))] / max(y_lista[0:int(vrijeme)])))), 5)
        font = pygame.font.Font(None, 20)
        tekst_surface = font.render(f"{int((int(vrijeme) * ((pozicija_misa[0] - 840) / 735)))}s, {round(y_lista[int((int(vrijeme) * ((pozicija_misa[0] - 840) / 735)))], 2)}{mjerna_jedinica}", False, "#C54640", None)
        tekst_rect = tekst_surface.get_rect(topleft = (pozicija_ishodista_grafa[0] + 15 + 550 * ((pozicija_misa[0] - 840) / 735), pozicija_ishodista_grafa[1] + 15 - (550*(y_lista[int(vrijeme * ((pozicija_misa[0] - 840) / 735))] / max(y_lista[0:int(vrijeme)])))))
        pygame.draw.rect(EKRAN, "#2B2B2B", (pozicija_ishodista_grafa[0] + 10 + 550 * ((pozicija_misa[0] - 840) / 735), pozicija_ishodista_grafa[1] + 11 - (550*(y_lista[int(vrijeme * ((pozicija_misa[0] - 840) / 735))] / max(y_lista[0:int(vrijeme)]))), tekst_rect.width + 10, tekst_rect.height + 8))
        EKRAN.blit(tekst_surface, tekst_rect)
    else:
        pygame.mouse.set_visible(True)

if __name__ == "__main__":
    main()