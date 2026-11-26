// Carrusel de la portada pública
let slideActual = 0;
let intervaloSlides = null;

function setSlide(indice) {
    const slides = document.querySelectorAll('.carousel-slide');
    const dots = document.querySelectorAll('.carousel-dot');
    if (!slides[indice]) return;

    slides[slideActual].classList.remove('active');
    dots[slideActual]?.classList.remove('w-8', 'bg-blue-500');
    dots[slideActual]?.classList.add('w-2', 'bg-white/40');

    slideActual = indice;

    slides[slideActual].classList.add('active');
    dots[slideActual]?.classList.remove('w-2', 'bg-white/40');
    dots[slideActual]?.classList.add('w-8', 'bg-blue-500');

    reiniciarAutoSlide();
}

// Avanza solo cada 4 segundos; se reinicia al elegir una diapositiva a mano
function reiniciarAutoSlide() {
    clearInterval(intervaloSlides);
    intervaloSlides = setInterval(() => {
        const total = document.querySelectorAll('.carousel-slide').length;
        if (total) setSlide((slideActual + 1) % total);
    }, 4000);
}

document.addEventListener('DOMContentLoaded', reiniciarAutoSlide);
