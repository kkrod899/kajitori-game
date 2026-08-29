# Codex working agreement

このリポジトリで作業するCodexは、最初に次の文書を順番に確認してください。

1. `HANDOFF.md`
2. `docs/PRODUCT_BRIEF.md`
3. `docs/COLLABORATION_WORKFLOW.md`
4. `docs/DECISIONS.md`
5. 依頼に対応する `reviews/` 内のレビュー

## 必須ルール

- `docs/PRODUCT_BRIEF.md` をプロダクト思想の正本とする。
- 表組などを活用し、視覚的な分かりやすさを重視する。
- ユーザーがレビューだけを求めている場合は、アプリ本体を変更しない。
- Claudeのレビューを受けて実装する場合、各指摘に `Accepted`、`Rejected`、`Deferred` のいずれかで応答する。
- 変更前に対象と影響範囲を確認し、変更後は対象に見合う検証を行う。
- 作業終了時に `HANDOFF.md` を更新する。
- 新しいプロダクト判断をした場合は `docs/DECISIONS.md` に追記する。
- 同じファイルをClaudeと同時に編集しない。

## レビュー担当時

- 実装を始めず、根拠付きの指摘を `reviews/` に残す。
- 重大度は `P0` から `P3` を使用する。
- 好みではなく、再現手順、影響、プロダクト原則との関係を示す。
- 指摘がない場合も、確認範囲と検証内容を記録する。
