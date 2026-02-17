// Footer Component
import { config } from '../config.js';

export function renderFooter() {
    return `
        <footer class="footer">
            <div class="container">
                <div class="footer-content">
                    <div class="footer-section">
                        <h3>Контакты</h3>
                        <div class="footer-contacts">
                            <div class="footer-item">
                                <div class="footer-item-icon">📞</div>
                                <div class="footer-item-text">
                                    <p>${config.CONTACT.phone}</p>
                                    <p>Приемная комиссия</p>
                                </div>
                            </div>
                            <div class="footer-item">
                                <div class="footer-item-icon">✉️</div>
                                <div class="footer-item-text">
                                    <p>${config.CONTACT.email}</p>
                                    <p>Приемная комиссия</p>
                                </div>
                            </div>
                            <div class="footer-item">
                                <div class="footer-item-icon">📍</div>
                                <div class="footer-item-text">
                                    <p>${config.CONTACT.address}</p>
                                    <p>главный корпус</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="footer-section">
                        <h3>Корпусы</h3>
                        <div class="footer-campuses">
                            ${config.CAMPUSES.map(campus => `
                                <div class="footer-item-text">
                                    <p>${campus.name}</p>
                                    <p>${campus.address}</p>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="footer-section">
                        <h3>О сайте</h3>
                        <div class="footer-about">
                            <p>Официальный сайт Казанского авиационно-технический колледжа имени П.В.Дементьева</p>
                            <p>© 2026 Все права защищены</p>
                            <p>Версия 1.5.0</p>
                        </div>
                    </div>
                </div>
                <div class="footer-bottom">
                    <p>Создано командой разработчиков ___ | Для связи: dev.constanta@gmail.com</p>
                </div>
            </div>
        </footer>
    `;
}

export function initFooter() {
    const footerEl = document.getElementById('footer');
    if (footerEl) {
        footerEl.innerHTML = renderFooter();
    }
}
