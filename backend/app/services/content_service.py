"""Service layer for support content (ECO-0607)."""

from typing import Any

from app.schemas.envelopes import SupportContentData, SupportContentEnvelope


class ContentService:
    async def get_support_content(self) -> SupportContentEnvelope:
        content: dict[str, Any] = {
            "faq": [
                {
                    "id": "faq-1",
                    "question": "Como funciona o aplicativo ECOconexão?",
                    "answer": (
                        "O ECOconexão permite explorar rotas de turismo sustentável, "
                        "conhecer iniciativas ecológicas locais e manter um histórico "
                        "das suas viagens."
                    ),
                    "category": "Geral",
                },
                {
                    "id": "faq-2",
                    "question": "O que é o Selo Verde de Empreendimento Consciente?",
                    "answer": (
                        "É um selo concedido aos estabelecimentos que cumprem critérios "
                        "rigorosos de sustentabilidade, gestão de resíduos e eficiência energética."
                    ),
                    "category": "Certificação",
                },
                {
                    "id": "faq-3",
                    "question": "Como registrar minhas viagens e visitas?",
                    "answer": (
                        "Ao iniciar uma rota, toque em 'Iniciar Viagem' no aplicativo. "
                        "Suas viagens e visitas serão salvas no histórico do seu perfil."
                    ),
                    "category": "Navegação",
                },
            ],
            "contacts": {
                "email": "suporte@econexao.org",
                "phone": "+55 82 3333-0000",
                "whatsapp": "+55 82 99999-0000",
                "operating_hours": "Segunda a Sexta, das 08:00 às 18:00",
            },
            "help_links": [
                {
                    "title": "Termos de Uso",
                    "url": "https://econexao.org/termos",
                },
                {
                    "title": "Política de Privacidade",
                    "url": "https://econexao.org/privacidade",
                },
                {
                    "title": "Guia de Acessibilidade",
                    "url": "https://econexao.org/acessibilidade",
                },
            ],
            "editorial_info": {
                "version": "1.0.0",
                "last_updated": "2026-08-12",
                "publisher": "SEMTUR & ECOconexão Editorial Team",
            },
        }
        return SupportContentEnvelope(data=SupportContentData.model_validate(content))
