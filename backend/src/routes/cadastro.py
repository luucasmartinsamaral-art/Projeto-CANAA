from flask import Blueprint, request, jsonify, send_file, send_from_directory
from src.models.cadastro import db, Cadastro
from datetime import datetime
import qrcode
import io
import base64
import os
import tempfile
from werkzeug.utils import secure_filename
import json

cadastro_bp = Blueprint("cadastro", __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_protocol():
    """Gera um protocolo único para o cadastro"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import random
    random_num = str(random.randint(100, 999))
    return f"CANAA-{timestamp}-{random_num}"

def generate_qr_code(protocol):
    """Gera QR code para o protocolo"""
    # URL para consulta do protocolo (pode ser personalizada)
    qr_data = f"https://projeto-canaa.com/consulta/{protocol}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Criar imagem do QR code
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Converter para base64
    img_buffer = io.BytesIO()
    img.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    return img_base64

@cadastro_bp.route("/cadastro", methods=["POST"])
def criar_cadastro():
    """Endpoint para criar um novo cadastro"""
    try:
        # Para lidar com dados de formulário e arquivos juntos
        data = request.form.to_dict()
        
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        # Gerar protocolo único
        protocolo = generate_protocol()
        
        # Verificar se o protocolo já existe (improvável, mas por segurança)
        while Cadastro.query.filter_by(protocolo=protocolo).first():
            protocolo = generate_protocol()
        
        # Criar diretório de upload se não existir
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        documentos_anexados = []
        if "documentos" in request.files:
            files = request.files.getlist("documentos")
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"{protocolo}_{file.filename}")
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    documentos_anexados.append(filename)
        
        # Converter data de nascimento
        data_nascimento = datetime.strptime(data["dataNascimento"], "%Y-%m-%d").date()
        
        # Parse JSON strings back to Python objects for nested data
        endereco_data = json.loads(data["endereco"])
        auto_declaracao_data = json.loads(data["autoDeclaracao"])

        # Criar novo cadastro
        novo_cadastro = Cadastro(
            protocolo=protocolo,
            nome_completo=data["nomeCompleto"],
            cpf=data["cpf"],
            rg=data["rg"],
            data_nascimento=data_nascimento,
            endereco_rua=endereco_data["rua"],
            endereco_numero=endereco_data["numero"],
            endereco_bairro=endereco_data["bairro"],
            endereco_cidade=endereco_data["cidade"],
            endereco_estado=endereco_data["estado"],
            endereco_cep=endereco_data["cep"],
            telefone=data["telefone"],
            tempo_fixacao=int(data["tempoFixacao"]),
            quantidade_pessoas=int(data["quantidadePessoas"]),
            moradores=data.get("moradores", ""),
            renda_familiar=float(data["rendaFamiliar"]),
            possui_imovel=data["possuiImovel"],
            programa_social=data["programaSocial"],
            auto_declaracao_pcd=auto_declaracao_data["pcd"],
            auto_declaracao_idoso=auto_declaracao_data["idoso"],
            auto_declaracao_outros=auto_declaracao_data["outros"],
            auto_declaracao_outros_descricao=auto_declaracao_data.get("outrosDescricao", ""),
            documentos=json.dumps(documentos_anexados) # Salvar como JSON string
        )
        
        # Salvar no banco de dados
        db.session.add(novo_cadastro)
        db.session.commit()
        
        # Gerar QR code
        qr_code_base64 = generate_qr_code(protocolo)
        
        return jsonify({
            "success": True,
            "protocolo": protocolo,
            "qr_code": qr_code_base64,
            "message": "Cadastro realizado com sucesso!"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao processar cadastro: {str(e)}"}), 500

@cadastro_bp.route("/consulta/<protocolo>", methods=["GET"])
def consultar_cadastro(protocolo):
    """Endpoint para consultar um cadastro pelo protocolo"""
    try:
        cadastro = Cadastro.query.filter_by(protocolo=protocolo).first()
        
        if not cadastro:
            return jsonify({"error": "Protocolo não encontrado"}), 404
        
        return jsonify({
            "success": True,
            "cadastro": cadastro.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erro ao consultar cadastro: {str(e)}"}), 500

@cadastro_bp.route("/qrcode/<protocolo>", methods=["GET"])
def gerar_qrcode(protocolo):
    """Endpoint para gerar QR code de um protocolo específico"""
    try:
        cadastro = Cadastro.query.filter_by(protocolo=protocolo).first()
        
        if not cadastro:
            return jsonify({"error": "Protocolo não encontrado"}), 404
        
        # Gerar QR code
        qr_data = f"https://projeto-canaa.com/consulta/{protocolo}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Criar imagem do QR code
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Salvar em arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        img.save(temp_file.name)
        temp_file.close()
        
        return send_file(temp_file.name, mimetype="image/png", as_attachment=True, 
                        download_name=f"qrcode_{protocolo}.png")
        
    except Exception as e:
        return jsonify({"error": f"Erro ao gerar QR code: {str(e)}"}), 500

@cadastro_bp.route("/cadastros", methods=["GET"])
def listar_cadastros():
    """Endpoint para listar todos os cadastros (para administração)"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        
        cadastros = Cadastro.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            "success": True,
            "cadastros": [cadastro.to_dict() for cadastro in cadastros.items],
            "total": cadastros.total,
            "pages": cadastros.pages,
            "current_page": page
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erro ao listar cadastros: {str(e)}"}), 500

@cadastro_bp.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


