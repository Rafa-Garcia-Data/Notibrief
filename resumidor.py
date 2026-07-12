import re
from collections import Counter


class Resumidor:
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.device = "cpu"

    def _split_sentences(self, text: str) -> list:
        sentences = re.split(r'(?<=[.!?;:])\s+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 15]

    def _score_sentences(self, sentences: list) -> list:
        all_words = []
        for s in sentences:
            words = re.findall(r'\w+', s.lower())
            all_words.extend(words)

        stop_words = {
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
            'de', 'del', 'al', 'en', 'con', 'por', 'para', 'sin',
            'es', 'son', 'esta', 'estan', 'hay', 'que', 'se', 'le',
            'lo', 'me', 'te', 'nos', 'mi', 'tu', 'su', 'sus',
            'y', 'o', 'pero', 'mas', 'ya', 'si', 'no', 'como',
            'muy', 'tambien', 'este', 'esta', 'eso', 'esto',
            'a', 'e', 'i', 'u', 'ante', 'bajo', 'contra', 'desde',
            'hacia', 'hasta', 'mediante', 'sobre', 'tras', 'entre',
            'todo', 'toda', 'todos', 'todas', 'otro', 'otra',
            'cuando', 'donde', 'quien', 'cual', 'cuyo',
            'ser', 'estar', 'haber', 'tener', 'hacer', 'poder',
            'ir', 'ver', 'dar', 'saber', 'querer', 'llegar',
            'pasar', 'deber', 'poner', 'parecer', 'quedar',
            'creer', 'hablar', 'llevar', 'dejar', 'seguir',
            'encontrar', 'llamar', 'venir', 'pensar', 'salir',
            'volver', 'tomar', 'conocer', 'vivir', 'sentir',
            'tratar', 'mirar', 'contar', 'empezar', 'esperar',
            'buscar', 'existir', 'entrar', 'trabajar', 'escribir',
            'perder', 'pagar', 'presentar', 'realizar', 'formar',
            'recibir', 'considerar', 'medio', 'puede', 'pueden',
            'mismo', 'misma', 'tan', 'mucho', 'poco', 'nada',
            'algo', 'siempre', 'nunca', 'aun', 'aunque',
        }

        word_freq = Counter(w for w in all_words if w not in stop_words and len(w) > 2)
        if not word_freq:
            return [(0, i, s) for i, s in enumerate(sentences)]

        max_freq = max(word_freq.values())
        for w in word_freq:
            word_freq[w] = word_freq[w] / max_freq

        scored = []
        for i, sentence in enumerate(sentences):
            words = re.findall(r'\w+', sentence.lower())
            if not words:
                scored.append((0, i, sentence))
                continue

            tf_score = sum(word_freq.get(w, 0) for w in words) / len(words)

            length_ok = 1.0
            if len(words) < 5:
                length_ok = 0.3
            elif len(words) > 40:
                length_ok = 0.7

            scored.append((tf_score * length_ok, i, sentence))

        return scored

    def resumir(self, texto: str, max_length: int = 300, min_length: int = 80) -> str:
        texto = re.sub(r"[\u2600-\u27BF\U0001F600-\U0001FAFF]", "", texto)
        texto = re.sub(r"\s+", " ", texto).strip()

        if not texto or len(texto) < 50:
            return texto if texto else ""

        sentences = self._split_sentences(texto)
        if not sentences:
            return texto[:max_length]

        if len(sentences) <= 2:
            return " ".join(sentences)

        scored = self._score_sentences(sentences)
        scored.sort(key=lambda x: x[0], reverse=True)

        num_sentences = max(3, min(6, len(sentences) // 2))

        selected = sorted(scored[:num_sentences], key=lambda x: x[1])

        result = " ".join(s for _, _, s in selected)

        if len(result) > max_length:
            truncated = result[:max_length]
            last = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
            if last > min_length:
                result = truncated[:last + 1]
            else:
                result = truncated.rsplit(" ", 1)[0] + "..."

        return result

    def resumir_post(self, post: dict) -> dict:
        texto = post.get("text", "")
        resumen = self.resumir(texto)
        return {**post, "resumen": resumen}

    def resumir_global(self, posts: list) -> str:
        textos = [p.get("text", "") for p in posts if len(p.get("text", "")) > 50]
        if not textos:
            return "No hay suficientes textos para generar un resumen global."
        texto_completo = " ".join(textos)
        return self.resumir(texto_completo, max_length=500, min_length=100)
