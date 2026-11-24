import { expect, test, type Page } from '@playwright/test'
import { installTauriMock, trackPageErrors } from './helpers/tauriMock'

const updateDialog = (page: Page) => page.getByRole('dialog', { name: 'Atualizações do Adito', exact: true })
const updateCalls = (page: Page) => page.evaluate(() =>
  ((window as unknown as Record<string, unknown>).__ADITO_MOCK_INVOKES__ || []) as string[],
)

test.describe('Distribuição: primeiro uso e atualizações', () => {
  test('sem nada novo, o aviso do canto não aparece', async ({ page }) => {
    await installTauriMock(page)
    await page.goto('/#/chat')
    await expect(page.getByLabel('Pergunta sobre pesquisa e extensão')).toBeVisible()
    await expect(page.getByTestId('atualizacao-disponivel')).toHaveCount(0)
    await expect(page.getByTestId('primeiro-uso-dados')).toHaveCount(0)
    await expect(updateDialog(page)).toHaveCount(0)
  })

  test('dados novos abrem aviso central automaticamente e só baixam após a escolha do usuário', async ({ page }) => {
    const errors = trackPageErrors(page)
    await installTauriMock(page, { dadosNovos: true })
    await page.goto('/#/chat')

    const painel = updateDialog(page)
    await expect(painel).toBeVisible()
    await expect(painel.getByText('Dados novos')).toBeVisible()
    await expect(painel.getByText(/2026-11-22/)).toBeVisible()
    const box = await painel.boundingBox()
    const viewport = page.viewportSize()!
    expect(box).not.toBeNull()
    expect(box!.width).toBeLessThan(viewport.width)
    expect(Math.abs(box!.x + box!.width / 2 - viewport.width / 2)).toBeLessThanOrEqual(2)
    expect(Math.abs(box!.y + box!.height / 2 - viewport.height / 2)).toBeLessThanOrEqual(2)
    expect(await updateCalls(page)).not.toContain('dados_instalar')

    await painel.getByRole('button', { name: 'Baixar agora', exact: true }).click()
    await expect(painel).toHaveCount(0)
    await expect(page.getByTestId('atualizacao-disponivel')).toHaveCount(0)
    expect(await updateCalls(page)).toContain('dados_instalar')
    expect(errors()).toEqual([])
  })

  test('adiar fecha o aviso, não repete ao navegar e permite reabri-lo pela sidebar', async ({ page }) => {
    await installTauriMock(page, { dadosNovos: true })
    await page.goto('/#/chat')
    const painel = updateDialog(page)
    await painel.getByRole('button', { name: 'Deixar para depois', exact: true }).click()
    await expect(painel).toHaveCount(0)
    const aviso = page.getByRole('button', { name: 'Atualização disponível', exact: true })
    await expect(aviso).toBeVisible()
    await page.getByRole('link', { name: 'Meu painel', exact: true }).click()
    await expect(page).toHaveURL(/#\/meu-dashboard/)
    await expect(painel).toHaveCount(0)
    await page.getByRole('link', { name: 'Chat', exact: true }).click()
    await expect(page.getByLabel('Pergunta sobre pesquisa e extensão')).toBeVisible()
    await expect(painel).toHaveCount(0)
    await aviso.click()
    await expect(painel).toBeVisible()
    expect(await updateCalls(page)).not.toContain('dados_instalar')
  })

  test('falha ao baixar dados mantém a mensagem de erro e permite tentar novamente ou adiar', async ({ page }) => {
    const errors = trackPageErrors(page)
    await installTauriMock(page, { dadosNovos: true, dadosErro: 'Falha de conexão ao baixar os dados.' })
    await page.goto('/#/chat')
    const painel = updateDialog(page)
    await painel.getByRole('button', { name: 'Baixar agora', exact: true }).click()
    await expect(painel.getByText('Falha de conexão ao baixar os dados.', { exact: true })).toBeVisible()
    await expect(painel.getByRole('button', { name: 'Baixar agora', exact: true })).toBeEnabled()
    await painel.getByRole('button', { name: 'Deixar para depois', exact: true }).click()
    await expect(painel).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Atualização disponível', exact: true })).toBeVisible()
    expect(errors()).toEqual([])
  })

  test('atualização do app usa download do plugin e solicita reinício após confirmação', async ({ page }) => {
    const errors = trackPageErrors(page)
    await installTauriMock(page, { appUpdate: true })
    await page.goto('/#/chat')
    const painel = updateDialog(page)
    await expect(painel.getByText(/0\.2\.0/)).toBeVisible()
    expect(await updateCalls(page)).not.toContain('plugin:updater|download_and_install')
    await painel.getByRole('button', { name: 'Baixar agora', exact: true }).click()
    await expect.poll(() => page.evaluate(() => sessionStorage.getItem('__adito_mock_restarted'))).toBe('true')
    const calls = await updateCalls(page)
    expect(calls).toContain('plugin:updater|download_and_install')
    expect(calls.indexOf('plugin:updater|download_and_install')).toBeLessThan(calls.indexOf('plugin:process|restart'))
    expect(errors()).toEqual([])
  })

  test('falha na atualização do app permanece no aviso sem solicitar reinício', async ({ page }) => {
    await installTauriMock(page, { appUpdate: true, appErro: 'Download interrompido.' })
    await page.goto('/#/chat')
    const painel = updateDialog(page)
    await painel.getByRole('button', { name: 'Baixar agora', exact: true }).click()
    await expect(painel.getByText('Não foi possível atualizar o app: Download interrompido.', { exact: true })).toBeVisible()
    await expect(painel.getByRole('button', { name: 'Baixar agora', exact: true })).toBeEnabled()
    expect(await updateCalls(page)).not.toContain('plugin:process|restart')
  })

  test('quando ambos estão disponíveis, atualiza os dados antes do app e do reinício', async ({ page }) => {
    await installTauriMock(page, { dadosNovos: true, appUpdate: true })
    await page.goto('/#/chat')
    await updateDialog(page).getByRole('button', { name: 'Baixar agora', exact: true }).click()
    await expect.poll(() => page.evaluate(() => sessionStorage.getItem('__adito_mock_restarted'))).toBe('true')
    const calls = await updateCalls(page)
    expect(calls.indexOf('dados_instalar')).toBeGreaterThanOrEqual(0)
    expect(calls.indexOf('dados_instalar')).toBeLessThan(calls.indexOf('plugin:updater|download_and_install'))
  })

  test('primeiro uso prioriza a chave dos dados antes do aviso de atualização do app', async ({ page }) => {
    await installTauriMock(page, { semDados: true, appUpdate: true })
    await page.goto('/#/chat')

    const tela = page.getByTestId('primeiro-uso-dados')
    await expect(tela).toBeVisible()
    await expect(updateDialog(page)).toHaveCount(0)
    const campo = tela.getByLabel('Chave dos dados')

    await campo.fill('b'.repeat(64))
    await tela.getByRole('button', { name: 'Baixar os dados' }).click()
    await expect(tela.getByText('Essa chave não abre esta versão dos dados.')).toBeVisible()

    await campo.fill('a'.repeat(64))
    await tela.getByRole('button', { name: 'Baixar os dados' }).click()
    await expect(tela).toHaveCount(0)
    await expect(updateDialog(page)).toBeVisible()
  })
})
