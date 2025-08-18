from enum import Enum

class DocType(Enum):
    XBRL = "XBRL"
    PDF = "PDF"
    ENGLISH = "ENGLISH"
    CSV = "CSV"

class RegalStatus(Enum):
    """
    縦覧ステータスを表すEnumクラス。
    """

    ON_VIEW = "1"  # 縦覧中
    EXTENDED = "2"  # 延長期間中
    EXPIRED = "0"  # 閲覧期間満了

    @staticmethod
    def from_string(value: str):
        for status in RegalStatus:
            if status.value == value:
                return status
        # 見つからなかった場合は例外を発生させる
        raise ValueError(f"'{value}' is not a valid RegalStatus value.")


class DisclosureStatus(Enum):
    """
    EDINET書類の開示ステータスを表すEnumクラス。
    """

    NOT_DISCLOSED_BY_STAFF = "1"  # 財務局職員によって書類の不開示を開始した情報
    NOT_DISCLOSED = "2"  # 不開示とされている書類
    DISCLOSURE_CANCELED = "3"  # 財務局職員によって書類の不開示を解除した情報
    OTHER = "0"  # それ以外

    @staticmethod
    def from_string(value: str):
        for status in RegalStatus:
            if status.value == value:
                return status
        # 見つからなかった場合は例外を発生させる
        raise ValueError(f"'{value}' is not a valid RegalStatus value.")


class PrefecturalOrdinanceCode(Enum):
    """
    内閣府令コード
    """

    KAISHI_NAIKAKUFUUREI = "010"  # 企業内容等の開示に関する内閣府令
    ZAIMU_KEISAN_JUISEI_KAKUHO_TAISEI = "015"  # 財務計算に関する書類その他の情報の適正性を確保するための体制に関する内閣府令
    GAIKOKUSAI_HAKKOUSHA_KAISHI = "020"  # 外国債等の発行者の開示に関する内閣府令
    TOKUTEI_YUUKASHOUKEN_NAIYOU_KAISHI = (
        "030"  # 特定有価証券の内容等の開示に関する内閣府令
    )
    HAKKOU_IGAI_KABUKEN_KOUKAIKAITSUKE_KAISHI = (
        "040"  # 発行者以外の者による株券等の公開買付けの開示に関する内閣府令
    )
    HAKKOU_JOUJOU_KABUKEN_KOUKAIKAITSUKE_KAISHI = (
        "050"  # 発行者による上場株券等の公開買付けの開示に関する内閣府令
    )
    KABUKEN_TAIRYUU_HOYU_KAISHI = "060"  # 株券等の大量保有の状況の開示に関する内閣府令


class DocumentTypeCode(Enum):
    """
    書類種別コード
    """

    YOUKASHOUKEN_TSUUCHISHO = "010"  # 有価証券通知書
    HENKOU_TSUUCHISHO_YOUKASHOUKEN = "020"  # 変更通知書（有価証券通知書）
    YOUKASHOUKEN_TODEDOKESHO = "030"  # 有価証券届出書
    TEISEI_YOUKASHOUKEN_TODEDOKESHO = "040"  # 訂正有価証券届出書
    TODEDOKEDE_TORISAGE_NEGAI = "050"  # 届出の取下げ願い
    HAKKOU_TOUROKU_TSUUCHISHO = "060"  # 発行登録通知書
    HENKOU_TSUUCHISHO_HAKKOU_TOUROKU = "070"  # 変更通知書（発行登録通知書）
    HAKKOU_TOUROKUSHO = "080"  # 発行登録書
    TEISEI_HAKKOU_TOUROKUSHO = "090"  # 訂正発行登録書
    HAKKOU_TOUROKU_TSUIHOSHORUI = "100"  # 発行登録追補書類
    HAKKOU_TOUROKU_TORISAGE_TODEDOKUSHO = "110"  # 発行登録取下届出書
    YOUKASHOUKEN_HOUKOKUSHO = "120"  # 有価証券報告書
    TEISEI_YOUKASHOUKEN_HOUKOKUSHO = "130"  # 訂正有価証券報告書
    KAKUNINSHO = "135"  # 確認書
    TEISEI_KAKUNINSHO = "136"  # 訂正確認書
    SHIHANKI_HOUKOKUSHO = "140"  # 四半期報告書
    TEISEI_SHIHANKI_HOUKOKUSHO = "150"  # 訂正四半期報告書
    HANGKI_HOUKOKUSHO = "160"  # 半期報告書
    TEISEI_HANGKI_HOUKOKUSHO = "170"  # 訂正半期報告書
    RINJI_HOUKOKUSHO = "180"  # 臨時報告書
    TEISEI_RINJI_HOUKOKUSHO = "190"  # 訂正臨時報告書
    OYAGAISHA_JOKYO_HOUKOKUSHO = "200"  # 親会社等状況報告書
    TEISEI_OYAGAISHA_JOKYO_HOUKOKUSHO = "210"  # 訂正親会社等状況報告書
    JIKO_KABUKEN_KAITSUKE_JOKYO_HOUKOKUSHO = "220"  # 自己株券買付状況報告書
    TEISEI_JIKO_KABUKEN_KAITSUKE_JOKYO_HOUKOKUSHO = "230"  # 訂正自己株券買付状況報告書
    NAIBU_TOUSEI_HOUKOKUSHO = "235"  # 内部統制報告書
    TEISEI_NAIBU_TOUSEI_HOUKOKUSHO = "236"  # 訂正内部統制報告書
    KOUKAITSUKE_TODEDOKESHO = "240"  # 公開買付届出書
    TEISEI_KOUKAITSUKE_TODEDOKESHO = "250"  # 訂正公開買付届出書
    KOUKAITSUKE_TEKKAI_TODEDOKUSHO = "260"  # 公開買付撤回届出書
    KOUKAITSUKE_HOUKOKUSHO = "270"  # 公開買付報告書
    TEISEI_KOUKAITSUKE_HOUKOKUSHO = "280"  # 訂正公開買付報告書
    IKEN_HYOMEI_HOUKOKUSHO = "290"  # 意見表明報告書
    TEISEI_IKEN_HYOMEI_HOUKOKUSHO = "300"  # 訂正意見表明報告書
    TSUI_SHITUMON_KAITOU_HOUKOKUSHO = "310"  # 対質問回答報告書
    TEISEI_TSUI_SHITUMON_KAITOU_HOUKOKUSHO = "320"  # 訂正対質問回答報告書
    BETTO_KAITSUKE_KINSHI_TOKUREI_MOUSHIDESHO = (
        "330"  # 別途買付け禁止の特例を受けるための申出書
    )
    TEISEI_BETTO_KAITSUKE_KINSHI_TOKUREI_MOUSHIDESHO = (
        "340"  # 訂正別途買付け禁止の特例を受けるための申出書
    )
    TAIRYUU_HOYU_HOUKOKUSHO = "350"  # 大量保有報告書
