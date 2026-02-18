// Application Configuration
export const config = {
    API_BASE: '/api',
    // S3_BASE_URL оставляем для будущего использования
    S3_BASE_URL: 'https://katk.s3.ru-7.storage.selcloud.ru',

    IMAGES_BASE: '/images',
    FALLBACK_IMAGE: '/images/specialty-placeholder.png',
    APP_NAME: 'КАТК им П.В. Дементьева',
    APP_TAGLINE: 'Построй свое будущее с нами',
    CONTACT: {
        phone: '+7(843) 571-35-30',
        email: 'pk@kaviat.ru',
        address: 'г Казань, ул. Копылова, дом 2б'
    },
    CAMPUSES: [
        { name: 'Учебный корпус №1', address: 'г. Казань, ул. Копылова, д. 2Б' },
        { name: 'Учебный корпус №2', address: 'г. Казань, ул. Дементьева, д. 26' },
        { name: 'Учебный корпус №3', address: 'г. Казань, ул. Химиков, д. 31а' }
    ]
};
